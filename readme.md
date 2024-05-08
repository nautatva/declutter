# Declutter

Tinder style app to quickly declutter photos from your library
- Has a left swipe feature to delete the photo
- Right swipe to accept it
- Top swipe to give a super like (favorite)


## Features
- Copy favorite photos to a common directory
- Buttons to move photos to bin/favorites

** Currently picks random photos from base path


## Structure
- Base folder (Specified in app.properties)
-- Album 1
--- Bin
-- Album 2
--- Bin

- Favorites (Specified in app.properites)


## Immediate plans
- Send only required dimension of photo, with option to load the complete photo on frontend
- Transactional (Undo a photo swipe)
- Pick an album (Or pick a random album) (Base path specified in app.properties)
- Change rating to 5 stars on original photo for favorites
- Infinite scrolling & Guestures
-- Move left swiped photos to `bin` folder
-- Double tap to like
-- Right swipe to do nothing
-- Swipe up to go to next photo
-- swipe down to decide previous photo again 


## Future plans
- AI Suggestions (redundant, blurry, or of low quality for deletion)
- Bulk Actions: Allow users to apply an action to multiple photos at once based on selection criteria (e.g., all photos taken in a certain location or within a specific date range).
- Tagging System: Incorporate a feature for users to tag photos during review. This could help with organizing photos more effectively, such as by event, people, location, etc.
- Statistics and Insights: Provide users with insights on their photo library, such as the amount of space saved, the number of photos deleted or favorited, and most common types of photos.
- Customizable Gestures: Allow users to customize what each swipe does (e.g., setting a right swipe for something other than acceptance, like tagging).
- Cloud Integration: Enable integration with cloud storage services for backing up accepted and favorite photos, offering additional security for saved photos.
- Smart Albums: Automatically create albums based on AI suggestions, such as grouping similar photos, creating timelines, or sorting by quality and relevance.
- Video support?
