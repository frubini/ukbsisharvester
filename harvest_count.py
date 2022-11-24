import logging
import config
from harvest import initial_harvest
from datetime import date

if __name__ == '__main__':
    logfile = date.toda().strftime('%Y-%m-%d_') + config.LOGFILE_SUFFIX
    logging.basicConfig(filename=logfile, filemode='a')
    logger = logging.getLogger(__name__)
    logger.setLevel(config.LOG_LEVEL)

    FILE_NAME = config.output_dir + date.today().strftime('/%Y-%m-%d_count.csv')

    initial_harvest('2020-05-01', True)
