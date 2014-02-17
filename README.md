# Reddit nxtip bot

This is the source code used for the reddit nxt tipping bot. The bot is based on [ALTCoinTip](https://github.com/vindimy/altcointip)
with additional Python modules that emulate the behavior of the bitcoind daemon, as far as ALTCoinTip is concerned.

## Introduction

For introduction to and use of ALTcointip bot, see __http://www.reddit.com/r/ALTcointip/wiki/index__

### Python Dependencies

The following Python libraries are necessary to run ALTcointip bot:

* __jinja2__ (http://jinja.pocoo.org/)
* __pifkoin__ (https://github.com/dpifke/pifkoin)
* __praw__ (https://github.com/praw-dev/praw)
* __sqlalchemy__ (http://www.sqlalchemy.org/)
* __yaml__ (http://pyyaml.org/wiki/PyYAML)
* __peewee__ (https://github.com/coleifer/peewee)
* __requests__ (https://github.com/kennethreitz/requests)

You can install `jinja2`, `praw`, `sqlalchemy`, `peewee` and `yaml` using `pip` (Python Package Index tool) or a package manager in your OS. For `pifkoin`, you'll need to copy or symlink its "python" subdirectory to `src/ctb/pifkoin`.

### Database

Create a new MySQL database instance for ALTCoinTip and run included SQL file [altcointip.sql](altcointip.sql) to create necessary tables. Create a MySQL user and grant it all privileges on the database. If you don't like to deal with command-line MySQL, use `phpMyAdmin`.

Create a new MySQL database instance for nxtip, enter the required information in src/ctb/nxtip_settings.py and run _create_nxtip_tables.py to create the necessary tables.

### Coin Daemons

Download and run NRS. Enter it's url in src/ctb/nxtip_settings.py (usually http://localhost:7874/nxt)

### Reddit Account

You should create a dedicated Reddit account for your bot. Initially, Reddit will ask for CAPTCHA input when bot posts a comment or message. To remove CAPTCHA requirement, the bot account needs to accumulate positive karma.

### Configuration

Edit `src/conf/*.yml` and src/ctb/nxtip_settings.py specifying necessary settings.

Most configuration options are described inline in provided sample configuration files.

### Running the Bot

1. Ensure MySQL is running and accepting connections given configured username/password
1. Ensure NRS daemon is running and responding to commands
1. Ensure Reddit authenticates configured user. _Note that from new users Reddit will require CAPTCHA responses when posting and sending messages. You will be able to type in CAPTCHA responses when required._
1. Execute `_start.sh` from [src](src/) directory. The command will not return for as long as the bot is running.
1. Execute `python ./ctb/nxtip_deposit.py` from [src](src/) directory. This command handles the deposits to the tipping bot. The command will not return for as long as the bot is running.

ALTcointip bot is configured by default to append INFO-level log messages to `logs/info.log`, and WARNING-level log messages to `logs/warning.log`, while DEBUG-level log messages are output to the console.
