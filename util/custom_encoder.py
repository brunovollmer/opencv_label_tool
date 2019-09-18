import json
import numpy as np

class CustomEncoder(json.JSONEncoder):
    """
    Custom Encoder, which is used to encode our results into JSON format.
    """
    def default(self, obj):
        """
        Default function, which es run before the JSONEncoder default function. Transfers numpy objects to lists so that the JSONEncoder can convert them to JSON.
        """
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return json.JSONEncoder.default(self, obj)