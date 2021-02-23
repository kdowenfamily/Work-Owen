import logging

LOGDIR = "/var/log/savings"
LOGFILE = LOGDIR + "/savings.log"

logging.basicConfig(filename=LOGFILE,
        format="[%(asctime)s] [%(levelname)-7s] [%(filename)s:%(lineno)d] %(message)s",
        level=logging.INFO)
log = logging.getLogger(__name__)
