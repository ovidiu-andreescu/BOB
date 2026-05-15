"""Service for generating trip recommendations."""


def get_recommendations(destination: str | None = None):
    """Get trip recommendations based on destination."""
    # Mock recommendations for demo purposes
    recommendations = [
        {
            "destination": "Paris",
            "description": "City of lights with amazing food and culture",
            "duration": 5,
        },
        {
            "destination": "Tokyo",
            "description": "Modern metropolis with traditional temples",
            "duration": 7,
        },
        {
            "destination": "Barcelona",
            "description": "Beautiful architecture and Mediterranean beaches",
            "duration": 4,
        },
    ]
    
    if destination:
        # Filter recommendations by destination
        recommendations = [
            r for r in recommendations
            if destination.lower() in r["destination"].lower()
        ]
    
    return recommendations

# Made with Bob
