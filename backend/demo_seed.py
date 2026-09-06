"""Synthetic local-only dataset, not an authentication bypass or production tool."""
import argparse
import os
from pathlib import Path
from database import db
from migrations import migrate
from models.user import UserRegister
from services.auth_service import register_user
from services.rating_service import create_or_update_rating
from models.rating import RatingCreate
from services.projection_service import save_review


def seed(path, password):
    if os.getenv('APP_ENV') not in {'development','test'}:
        raise RuntimeError('Demo seed requires explicit APP_ENV=development or test')
    path=Path(path).resolve()
    if path.exists():
        raise RuntimeError('Refusing existing database; choose a new disposable path')
    if len(password)<12:
        raise RuntimeError('Demo password must have at least 12 characters')
    # Atomic filesystem reservation prevents accidentally adopting an existing DB.
    with path.open('xb'):
        pass
    migrate(str(path),initialize=True)
    previous=db.db_path
    db.db_path=str(path)
    try:
        with db.transaction():
            db.execute_update('CREATE TABLE demo_dataset(label TEXT NOT NULL)')
            db.execute_insert("INSERT INTO demo_dataset VALUES ('SYNTHETIC LOCAL DEMO - NEVER PRODUCTION')")
            for id in range(1,41):
                db.execute_insert("""INSERT INTO anime(id,title_romaji,title_english,title_native,title_korean,
                    format,status,description,season,season_year,episodes,duration,average_score,popularity,cover_image_url)
                    VALUES (?,?,?,?,?,'TV','FINISHED',?,'SPRING',2026,12,24,80,?,?)""",
                    (id,f'Synthetic Journey {id}',f'Synthetic Journey {id}',f'合成の旅 {id}',f'합성 여행 {id}',
                     'Local synthetic anime for interaction testing. 실제 작품이 아닙니다.',10000-id,'/demo-assets/poster.svg'))
                db.execute_insert('INSERT INTO character(id,name_full,name_native,name_korean,description,favourites,image_url) VALUES (?,?,?,?,?,?,?)',
                    (id,f'Demo Character {id}',f'合成人物 {id}',f'데모 캐릭터 {id}','Synthetic local character',1000-id,'/demo-assets/poster.svg'))
                db.execute_insert("INSERT INTO anime_character VALUES (?,?,'MAIN')",(id,id))
            db.execute_insert("INSERT INTO genre(id,name) VALUES (1,'Adventure'),(2,'Fantasy')")
            for id in range(1,41):
                db.execute_insert('INSERT INTO anime_genre VALUES (?,?)',(id,1 if id%2 else 2))
            account=register_user(UserRegister(username='anibitedemo',email='anibite-demo@example.com',password=password,display_name='[DEMO] 합성 테스트 계정'))
            for id in range(1,5):
                create_or_update_rating(account.user.id,RatingCreate(anime_id=id,rating=4.5,status='RATED'))
            save_review('anime',account.user.id,1,'[DEMO] Synthetic review','This is an explicitly synthetic review for local UX testing only.',False)
    finally:
        db.db_path=previous


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database',required=True,help='NEW disposable local sqlite path')
    args=parser.parse_args()
    password=os.getenv('DEMO_PASSWORD')
    if not password:
        raise SystemExit('Set DEMO_PASSWORD explicitly (at least 12 characters)')
    seed(args.database,password)
    print('Synthetic local demo created. Username: anibitedemo. Password: supplied DEMO_PASSWORD. No external APIs called.')

if __name__=='__main__':
    main()
