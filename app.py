
from flask import Flask, jsonify, request
from flask_cors import CORS
from hentai_scraper import HentaiTVScraper
import logging
import os

app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

scraper = HentaiTVScraper()


# -----------------------------------------------------------------------
# Helper functions
# -----------------------------------------------------------------------
def _ok(data, **extra):
    return jsonify({
        "success": True,
        "data": data,
        **extra
    })


def _err(msg, code=500):
    return jsonify({
        "success": False,
        "error": str(msg)
    }), code


# -----------------------------------------------------------------------
# Homepage (GET /)
# -----------------------------------------------------------------------
@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "success": True,
        "message": "H-A API is running!",
        "endpoints": {
            "recent": "/api/recent?page=1",
            "trending": "/api/trending?page=1",
            "search": "/api/search?q=test&page=1",
            "genres": "/api/genres",
            "genre": "/api/genre/<slug>?page=1",
            "details": "/api/details/<slug>"
        }
    })


# -----------------------------------------------------------------------
# Health check (GET /health)
# -----------------------------------------------------------------------
@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "success": True,
        "status": "healthy"
    })


# -----------------------------------------------------------------------
# Recent / Browse (GET /api/recent?page=N)
# -----------------------------------------------------------------------
@app.route("/api/recent", methods=["GET"])
async def get_recent():
    page = request.args.get("page", 1, type=int)

    if page < 1:
        return _err("Page must be 1 or greater", 400)

    try:
        result = await scraper.get_recent(page=page)

        return jsonify({
            "success": True,
            "data": result["videos"],
            "total": result["total"],
            "pages": result["pages"],
            "page": page
        })

    except Exception:
        logger.exception("Error fetching recent videos")
        return _err("Failed to fetch recent videos. Please try again later.")


# -----------------------------------------------------------------------
# Trending (GET /api/trending?page=N)
# -----------------------------------------------------------------------
@app.route("/api/trending", methods=["GET"])
async def get_trending():
    page = request.args.get("page", 1, type=int)

    if page < 1:
        return _err("Page must be 1 or greater", 400)

    try:
        result = await scraper.get_trending(page=page)

        return jsonify({
            "success": True,
            "data": result["videos"],
            "total": result["total"],
            "pages": result["pages"],
            "page": page
        })

    except Exception:
        logger.exception("Error fetching trending videos")
        return _err("Failed to fetch trending videos. Please try again later.")


# -----------------------------------------------------------------------
# Search (GET /api/search?q=QUERY&page=N)
# -----------------------------------------------------------------------
@app.route("/api/search", methods=["GET"])
async def search():
    query = request.args.get("q", "").strip()
    page = request.args.get("page", 1, type=int)

    if not query:
        return _err("Query parameter 'q' is required", 400)

    if page < 1:
        return _err("Page must be 1 or greater", 400)

    try:
        videos = await scraper.search(query, page=page)
        return _ok(videos, page=page)

    except Exception:
        logger.exception("Error searching videos")
        return _err("Search failed. Please try again later.")


# -----------------------------------------------------------------------
# Genres (GET /api/genres)
# -----------------------------------------------------------------------
@app.route("/api/genres", methods=["GET"])
async def get_genres():
    try:
        genres = await scraper.get_genres()
        return _ok(genres)

    except Exception:
        logger.exception("Error fetching genres")
        return _err("Failed to fetch genres. Please try again later.")


# -----------------------------------------------------------------------
# Genre / Tag videos (GET /api/genre/<slug>?page=N)
# -----------------------------------------------------------------------
@app.route("/api/genre/<slug>", methods=["GET"])
async def get_by_genre(slug):
    page = request.args.get("page", 1, type=int)

    if page < 1:
        return _err("Page must be 1 or greater", 400)

    try:
        result = await scraper.get_by_tag(slug, page=page)

        return jsonify({
            "success": True,
            "data": result["videos"],
            "total": result["total"],
            "pages": result["pages"],
            "page": page
        })

    except Exception:
        logger.exception("Error fetching genre videos")
        return _err("Failed to fetch genre videos. Please try again later.")


# -----------------------------------------------------------------------
# Video details (GET /api/details/<slug>)
# -----------------------------------------------------------------------
@app.route("/api/details/<slug>", methods=["GET"])
async def get_details(slug):
    try:
        details = await scraper.get_video_details(slug)
        return _ok(details)

    except Exception:
        logger.exception("Error fetching video details")
        return _err("Failed to fetch video details. Please try again later.")


# -----------------------------------------------------------------------
# Handle unknown routes
# -----------------------------------------------------------------------
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "success": False,
        "error": "Endpoint not found",
        "available_endpoints": [
            "/",
            "/health",
            "/api/recent",
            "/api/trending",
            "/api/search?q=test",
            "/api/genres",
            "/api/genre/<slug>",
            "/api/details/<slug>"
        ]
    }), 404


# -----------------------------------------------------------------------
# Main (for local development)
# -----------------------------------------------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
