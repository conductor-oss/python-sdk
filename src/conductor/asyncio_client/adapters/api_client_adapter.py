import datetime
import decimal
import re
from enum import Enum

from conductor.asyncio_client.http.api_client import ApiClient


class ApiClientAdapter(ApiClient):
    def __deserialize(self, data, klass):
        """Deserializes dict, list, str into an object.

        :param data: dict, list or str.
        :param klass: class literal, or string of class name.

        :return: object.
        """
        if data is None:
            return None

        if isinstance(klass, str):
            if klass.startswith("List["):
                m = re.match(r"List\[(.*)]", klass)
                assert m is not None, "Malformed List type definition"
                sub_kls = m.group(1)
                return [self.__deserialize(sub_data, sub_kls) for sub_data in data]

            if klass.startswith("Dict["):
                m = re.match(r"Dict\[([^,]*), (.*)]", klass)
                assert m is not None, "Malformed Dict type definition"
                sub_kls = m.group(2)
                return {k: self.__deserialize(v, sub_kls) for k, v in data.items()}

            # convert str to class
            if klass in self.NATIVE_TYPES_MAPPING:
                klass = self.NATIVE_TYPES_MAPPING[klass]
            else:
                klass = getattr(conductor.asyncio_client.adapters.models, klass)

        if klass in self.PRIMITIVE_TYPES:
            return self.__deserialize_primitive(data, klass)
        elif klass == object:
            return self.__deserialize_object(data)
        elif klass == datetime.date:
            return self.__deserialize_date(data)
        elif klass == datetime.datetime:
            return self.__deserialize_datetime(data)
        elif klass == decimal.Decimal:
            return decimal.Decimal(data)
        elif issubclass(klass, Enum):
            return self.__deserialize_enum(data, klass)
        else:
            return self.__deserialize_model(data, klass)
