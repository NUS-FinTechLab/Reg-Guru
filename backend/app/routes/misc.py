"""Miscellaneous handlers like health checks and CORS helpers."""

from __future__ import annotations

from flask import jsonify

from . import api


@api.route("/<path:path>", methods=["OPTIONS"])
def options_handler(path):
    """Handle CORS preflight requests."""
    response = jsonify({"success": True})
    response.headers.add("Access-Control-Allow-Origin", "http://localhost:3000")
    response.headers.add("Access-Control-Allow-Headers", "Content-Type")
    return response


@api.route("/test")
def test():
    """Test endpoint to verify API is working."""
    return jsonify({"message": "Test successful"}), 200
