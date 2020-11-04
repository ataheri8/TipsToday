import rapidjson
import traceback

from app.common import logger



def parse(str):
    try:
        return rapidjson.loads(str)
    except:
        return None


def stringify(data):
    if data:
        try:
            return rapidjson.dumps(data,
                                   datetime_mode=rapidjson.DM_ISO8601 | rapidjson.DM_NAIVE_IS_UTC,
                                   number_mode=rapidjson.NM_DECIMAL,
                                   uuid_mode=rapidjson.UM_CANONICAL)
        except:  # pragma: no cover
            # Can't convert to json, so log it and give a blank object
            logger.error("Unable to convert data to json: ", data=data)
            logger.exception(traceback.format_exc())

    return None
