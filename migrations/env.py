from __future__ import annotations

from logging.config import fileConfig

from alembic import context

from app import create_app
from app.extensions import db

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    logging_sections = {'loggers', 'handlers', 'formatters'}
    if logging_sections.issubset(set(config.file_config.sections())):
        fileConfig(config.config_file_name)

app = create_app()


def get_metadata():
    return db.metadata


def get_url() -> str:
    with app.app_context():
        return str(db.engine.url)


def run_migrations_offline() -> None:
    url = get_url()
    context.configure(
        url=url,
        target_metadata=get_metadata(),
        literal_binds=True,
        dialect_opts={'paramstyle': 'named'},
        render_as_batch=url.startswith('sqlite'),
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    with app.app_context():
        connectable = db.engine

        with connectable.connect() as connection:
            context.configure(
                connection=connection,
                target_metadata=get_metadata(),
                render_as_batch=connection.dialect.name == 'sqlite',
            )

            with context.begin_transaction():
                context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
