"""Static deployment safety gates; never execute a DB/bootstrap script."""
from pathlib import Path
import tomllib
import unittest

ROOT = Path(__file__).resolve().parents[2]


def config(name):
    return tomllib.loads((ROOT / name).read_text())


class DeployConfigTests(unittest.TestCase):
    def test_deployment_contexts_exclude_private_local_artifacts(self):
        required = {
            '*.db', '**/*.db', '*.db-*', '**/*.db-*',
            '*.sqlite*', '**/*.sqlite*', '.env', '**/.env',
            '.env.*', '**/.env.*', '*.env', '**/*.env',
            '.venv/', '**/.venv/', 'venv/', '**/venv/',
            '**/test-results/', '**/playwright-report/',
            '**/node_modules/', '**/__pycache__/',
            '.vercel/', '**/.vercel/', 'data/backups/',
        }
        for name in ('.dockerignore', '.railwayignore'):
            with self.subTest(file=name):
                path = ROOT / name
                self.assertTrue(path.is_file(), f'{name} must exist')
                patterns = {line.strip() for line in path.read_text().splitlines()
                            if line.strip() and not line.lstrip().startswith('#')}
                self.assertFalse(required - patterns,
                                 f'{name} missing exclusions: {sorted(required - patterns)}')
                self.assertFalse(any(line.startswith('!') and
                                     any(token in line for token in ('.db', '.env', '.sqlite'))
                                     for line in patterns))

    def test_railway_explicitly_gates_worker_readiness(self):
        deploy = config('railway.toml')['deploy']
        self.assertEqual(deploy.get('startCommand'), 'bash /app/docker-startup.sh')
        self.assertEqual(deploy.get('healthcheckPath'), '/ready')
        self.assertNotIn('preDeployCommand', deploy)

    def test_railway_uses_explicit_python_docker_artifact(self):
        self.assertEqual(config('railway.toml')['build'],
                         {'builder': 'DOCKERFILE', 'dockerfilePath': 'Dockerfile'})
        self.assertNotIn('volumeMountPath', config('railway.toml')['deploy'])

    def test_build_runtime_matches_supported_release(self):
        self.assertEqual(config('nixpacks.toml')['phases']['setup']['nixPkgs'],
                         ['nodejs_22', 'python311'])

    def test_nixpacks_uses_check_only_canonical_startup(self):
        self.assertEqual(config('nixpacks.toml')['start']['cmd'],
                         'bash /app/docker-startup.sh')
        startup = (ROOT / 'docker-startup.sh').read_text()
        self.assertIn('python -m migrations check', startup)
        for forbidden in ('download_db', 'init_db', 'migrations migrate', 'migrations init'):
            self.assertNotIn(forbidden, startup)


if __name__ == '__main__':
    unittest.main()
