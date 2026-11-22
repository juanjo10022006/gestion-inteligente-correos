"""Append-only event publication with a durable, per-message outbox."""

from datetime import datetime, timezone

from bson import ObjectId
from fastapi import HTTPException
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError

LEGACY_FIELDS = (
    "creationEvent", "classificationEvent", "manualEvent", "managementEvent", "closureEvent",
)
SNAPSHOT_FIELDS = ("status", "department", "prediction", "assignmentOrigin", "assignment", "resolution")


def snapshot(document):
    # Never copy subject/body, account secrets or internal delivery state into events.
    return {key: document.get(key) for key in SNAPSHOT_FIELDS}


def make_event(message_id, action, actor, before, after, reason=None):
    return {
        "_id": ObjectId(),
        "messageId": str(message_id),
        "actorType": "SISTEMA" if actor is None else "USUARIO",
        "actorUserId": actor if actor is not None else "SISTEMA",
        "action": action,
        "createdAt": datetime.now(timezone.utc),
        "before": before,
        "after": after,
        "reason": reason,
    }


def publish_pending(database, message_id=None):
    query = {"pendingAudit.0": {"$exists": True}}
    if message_id is not None:
        query["_id"] = ObjectId(message_id)
    for message in database.messages.find(query, {"pendingAudit": 1}):
        for event in message["pendingAudit"]:
            try:
                database.audit_events.insert_one(event)
            except DuplicateKeyError:
                # An interrupted delivery may already have inserted this exact event.
                if database.audit_events.find_one({"_id": event["_id"]}) != event:
                    raise
            database.messages.update_one(
                {"_id": message["_id"]}, {"$pull": {"pendingAudit": {"_id": event["_id"]}}},
            )


def update_with_events(database, before, updates, events):
    """CAS protects before/after; document change and delivery intent are one write."""
    query = {"_id": before["_id"], "status": before["status"]}
    query["revision"] = before["revision"] if "revision" in before else {"$exists": False}
    document = database.messages.find_one_and_update(
        query,
        {"$set": updates, "$inc": {"revision": 1}, "$push": {"pendingAudit": {"$each": events}}},
        return_document=ReturnDocument.AFTER,
    )
    if document is None:
        raise HTTPException(409, "El mensaje cambió durante la operación. Actualiza e intenta de nuevo.")
    publish_pending(database, before["_id"])
    return document


def event_pipeline(filters, limit):
    stored_filters = dict(filters)
    if "messageId" in filters:
        stored_filters["messageId"] = {"$in": [filters["messageId"], ObjectId(filters["messageId"])]}
    legacy = [
        {"$project": {
            "messageId": {"$toString": "$_id"},
            "events": [{"$ifNull": [f"${field}", None]} for field in LEGACY_FIELDS],
        }},
        {"$unwind": {"path": "$events", "includeArrayIndex": "eventIndex"}},
        {"$match": {"events": {"$ne": None}}},
        {"$project": {
            "_id": {"$concat": ["legacy:", "$messageId", ":", {"$toString": "$eventIndex"}]},
            "messageId": 1,
            "action": "$events.action",
            "actorUserId": "$events.actorUserId",
            "actorType": {"$cond": [
                {"$eq": ["$events.actorUserId", "SISTEMA"]}, "SISTEMA", "USUARIO",
            ]},
            "createdAt": "$events.createdAt",
            "reason": {"$ifNull": ["$events.reason", None]},
            "before": {"$literal": None},
            "after": {"$literal": None},
            "source": {"$literal": "LEGACY"},
        }},
    ]
    if "messageId" in filters:
        legacy.insert(0, {"$match": {"_id": ObjectId(filters["messageId"])}})
    return [
        {"$match": stored_filters},
        {"$addFields": {
            "_id": {"$toString": "$_id"},
            "messageId": {"$toString": "$messageId"},
            "source": {"$literal": "HISTORICAL"},
        }},
        {"$unionWith": {"coll": "messages", "pipeline": legacy}},
        {"$match": filters},
        {"$sort": {"createdAt": -1, "_id": -1}},
        {"$limit": limit},
        {"$set": {"id": "$_id"}},
        {"$unset": "_id"},
    ]
