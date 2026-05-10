from bson import ObjectId


def serialize(doc):
    if isinstance(doc, list):
        return [serialize(d) for d in doc]
    if isinstance(doc, dict):
        return {k: serialize(v) for k, v in doc.items()}
    if isinstance(doc, ObjectId):
        return str(doc)
    return doc


def to_object_ids(id_list):
    result = []
    for i in id_list:
        try:
            result.append(ObjectId(i))
        except Exception:
            pass
    return result
