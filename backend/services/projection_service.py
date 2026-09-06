"""Single service-owned activity projection; source rating/review IDs stay intact."""
from database import db
from fastapi import HTTPException


def sources(kind):
    if kind == 'anime':
        return 'user_ratings','user_reviews','anime_id','anime'
    if kind == 'character':
        return 'character_ratings','character_reviews','character_id','character'
    raise ValueError('Unsupported rating kind')


@db.atomic
def sync_projection(kind, user_id, item_id):
    ratings,reviews,key,items = sources(kind)
    user=db.execute_query('SELECT u.*,COALESCE(s.otaku_score,0) AS otaku_score FROM users u LEFT JOIN user_stats s ON s.user_id=u.id WHERE u.id=?',(user_id,),fetch_one=True)
    item=db.execute_query(f'SELECT * FROM {items} WHERE id=?',(item_id,),fetch_one=True)
    rating=db.execute_query(f'SELECT * FROM {ratings} WHERE user_id=? AND {key}=?',(user_id,item_id),fetch_one=True)
    review=db.execute_query(f'SELECT * FROM {reviews} WHERE user_id=? AND {key}=?',(user_id,item_id),fetch_one=True)
    if not user or not item:
        raise HTTPException(status_code=404,detail='User or item not found')
    valid_rating=rating['rating'] if rating and rating['status']=='RATED' else None
    if valid_rating is None and not review:
        db.execute_update("UPDATE activities SET rating=NULL,review_title=NULL,review_content=NULL WHERE activity_type=? AND user_id=? AND item_id=?",(kind+'_rating',user_id,item_id))
        return
    item=dict(item)
    parent=None
    if kind=='character':
        parent=db.execute_query("SELECT a.* FROM anime a JOIN anime_character ac ON ac.anime_id=a.id WHERE ac.character_id=? ORDER BY CASE ac.role WHEN 'MAIN' THEN 0 ELSE 1 END,a.popularity DESC,a.id LIMIT 1",(item_id,),fetch_one=True)
    data={
        'activity_type':kind+'_rating','user_id':user_id,'item_id':item_id,
        'username':user['username'],'display_name':user['display_name'],'avatar_url':user['avatar_url'],'otaku_score':user['otaku_score'],
        'item_title':item.get('title_romaji') if kind=='anime' else item.get('name_full'),
        'item_title_korean':item.get('title_korean') if kind=='anime' else item.get('name_korean'),
        'item_title_native':item.get('title_native') if kind=='anime' else item.get('name_native'),
        'item_image':item.get('cover_image_url') if kind=='anime' else item.get('image_url'),
        'item_year':item.get('season_year'),'rating':valid_rating,
        'review_title':review['title'] if review else None,'review_content':review['content'] if review else None,
        'is_spoiler':review['is_spoiler'] if review else 0,
        'anime_id':parent['id'] if parent else None,'anime_title':parent['title_romaji'] if parent else None,
        'anime_title_korean':parent['title_korean'] if parent else None,'anime_title_native':parent['title_native'] if parent else None,
    }
    columns=','.join(data)
    updates=','.join(f'{k}=excluded.{k}' for k in data if k not in {'activity_type','user_id','item_id'})
    db.execute_update(f"""INSERT INTO activities({columns},activity_time) VALUES ({','.join('?' for _ in data)},CURRENT_TIMESTAMP)
        ON CONFLICT(activity_type,user_id,item_id) DO UPDATE SET {updates},updated_at=CURRENT_TIMESTAMP""",tuple(data.values()))


@db.atomic
def save_review(kind,user_id,item_id,title,content,is_spoiler=False,rating=None):
    ratings,reviews,key,items=sources(kind)
    if not content or not 10<=len(content.strip())<=5000 or title is not None and len(title)>100:
        raise HTTPException(status_code=422,detail='Review requires 10–5000 characters and title at most 100')
    if not db.execute_query(f'SELECT id FROM {items} WHERE id=?',(item_id,),fetch_one=True):
        raise HTTPException(status_code=404,detail='Item not found')
    if rating is not None:
        if kind=='anime':
            from services.rating_service import create_or_update_rating
            from models.rating import RatingCreate
            create_or_update_rating(user_id,RatingCreate(anime_id=item_id,rating=rating,status='RATED'))
        else:
            from services.character_service import create_or_update_character_rating
            create_or_update_character_rating(user_id,item_id,rating,'RATED')
    db.execute_update(f"""INSERT INTO {reviews}(user_id,{key},title,content,is_spoiler) VALUES (?,?,?,?,?)
        ON CONFLICT(user_id,{key}) DO UPDATE SET title=excluded.title,content=excluded.content,
        is_spoiler=excluded.is_spoiler,updated_at=CURRENT_TIMESTAMP""",(user_id,item_id,title,content,bool(is_spoiler)))
    sync_projection(kind,user_id,item_id)
    from services.rating_service import _update_user_stats
    _update_user_stats(user_id)
    return db.execute_query(f'SELECT id FROM {reviews} WHERE user_id=? AND {key}=?',(user_id,item_id),fetch_one=True)[0]
