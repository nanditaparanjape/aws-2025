// Global variables
let currentSong = null;
let cachedRecommendations = null;
let lastRecommendationTime = 0;
const MIN_RECOMMENDATION_INTERVAL = 15000; // 15 seconds between recommendation fetches
let isUpdating = false; // Flag to prevent multiple simultaneous updates

// Handle form submission on index page
document.addEventListener('DOMContentLoaded', function() {
    // Handle form submission on index page
    const songForm = document.getElementById('songForm');
    if (songForm) {
        songForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            const title = document.getElementById('title').value;
            const artist = document.getElementById('artist').value;

            try {
                const response = await fetch('/vibe', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ title, artist })
                });

                const data = await response.json();
                if (data.success) {
                    currentSong = data.song;
                    localStorage.setItem('currentSong', JSON.stringify(data.song));
                    window.location.href = 'initial_card.html';
                } else {
                    alert('Error: ' + data.error);
                }
            } catch (error) {
                console.error('Error:', error);
                alert('An error occurred while processing your request.');
            }
        });
    }

    // Handle initial card page
    if (window.location.pathname.includes('initial_card.html')) {
        const storedSong = localStorage.getItem('currentSong');
        if (storedSong) {
            const song = JSON.parse(storedSong);
            // Update the card with song details
            const cardImage = document.querySelector('.card-image');
            const songTitle = document.querySelector('.song-title');
            const artistName = document.querySelector('.artist-name');
            const bpmValue = document.querySelector('.detail-item:nth-child(1) .detail-value');
            const keyValue = document.querySelector('.detail-item:nth-child(2) .detail-value');
            const durationValue = document.querySelector('.detail-item:nth-child(3) .detail-value');

            if (cardImage) cardImage.src = song.image;
            if (songTitle) songTitle.textContent = song.title;
            if (artistName) artistName.textContent = song.artist;
            if (bpmValue) bpmValue.textContent = song.bpm;
            if (keyValue) keyValue.textContent = song.key;
            if (durationValue) durationValue.textContent = song.duration;
        }
    }

    // Handle in_set page
    if (window.location.pathname.includes('in_set.html')) {
        // Set initial current song
        const storedSong = localStorage.getItem('currentSong');
        if (storedSong) {
            const song = JSON.parse(storedSong);
            const bottomCard = document.querySelector('.bottom-card');
            if (bottomCard) {
                bottomCard.querySelector('.song-img').src = song.image;
                bottomCard.querySelector('.song-name').textContent = song.title;
                bottomCard.querySelector('.artist-name').textContent = song.artist;
                bottomCard.querySelector('.song-length').textContent = song.duration;
            }
        }
        
        // Get initial recommendations only once
        updateRecommendations();
        
        // Handle end set button
        const endSetBtn = document.querySelector('.end-set-btn');
        if (endSetBtn) {
            endSetBtn.addEventListener('click', async function() {
                try {
                    const response = await fetch('/end_set', {
                        method: 'POST'
                    });
                    const data = await response.json();
                    if (data.success) {
                        // Show completion message
                        const completionMessage = document.getElementById('completion-message');
                        if (completionMessage) {
                            completionMessage.style.display = 'block';
                        }
                        
                        // Hide other elements
                        document.querySelector('.song-choices').style.display = 'none';
                        document.querySelector('.bottom-card').style.display = 'none';
                        endSetBtn.style.display = 'none';
                    }
                } catch (error) {
                    console.error('Error:', error);
                    alert('An error occurred while ending the set.');
                }
            });
        }
    }
});

function selectSong(card) {
    const title = card.querySelector('.song-title').textContent;
    const artist = card.querySelector('.artist-name').textContent;
    const image = card.querySelector('.card-image').src;
    const duration = card.querySelector('.detail-item:nth-child(3) .detail-value').textContent;
    
    // Update the bottom card immediately
    const bottomCard = document.querySelector('.bottom-card');
    if (bottomCard) {
        bottomCard.querySelector('.song-img').src = image;
        bottomCard.querySelector('.song-name').textContent = title;
        bottomCard.querySelector('.artist-name').textContent = artist;
        bottomCard.querySelector('.song-length').textContent = duration;
    }
    
    // Store the new current song
    const currentSong = {
        title: title,
        artist: artist,
        image: image,
        duration: duration
    };
    localStorage.setItem('currentSong', JSON.stringify(currentSong));
    
    // Show "Please wait..." in all recommendation cards
    const cards = document.querySelectorAll('.choice-card, .choice-card1, .choice-card2');
    cards.forEach(card => {
        card.querySelector('.song-title').textContent = 'Please wait...';
        card.querySelector('.artist-name').textContent = 'New recommendations coming soon';
        card.querySelector('.detail-item:nth-child(1) .detail-value').textContent = '...';
        card.querySelector('.detail-item:nth-child(2) .detail-value').textContent = '...';
        card.querySelector('.detail-item:nth-child(3) .detail-value').textContent = '...';
        card.querySelector('.detail-item:nth-child(4) .detail-value').textContent = '...';
    });
    
    // Schedule the recommendation update
    const now = Date.now();
    const timeSinceLastUpdate = now - lastRecommendationTime;
    const timeToWait = Math.max(0, MIN_RECOMMENDATION_INTERVAL - timeSinceLastUpdate);
    
    if (timeToWait > 0) {
        console.log(`Waiting ${timeToWait/1000} seconds before updating recommendations...`);
        setTimeout(updateRecommendations, timeToWait);
    } else {
        updateRecommendations();
    }
}

async function updateRecommendations() {
    // Prevent multiple simultaneous updates
    if (isUpdating) {
        console.log('Update already in progress...');
        return;
    }

    try {
        isUpdating = true;
        const now = Date.now();
        
        // Check rate limiting
        if (now - lastRecommendationTime < MIN_RECOMMENDATION_INTERVAL) {
            console.log('Waiting for rate limit...');
            return;
        }
        
        lastRecommendationTime = now;
        
        const response = await fetch('/get_recommendations', {
            method: 'POST'
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.success) {
            cachedRecommendations = data.recommendations;
            updateRecommendationCards(data.recommendations);
        } else {
            console.error('Failed to get recommendations:', data.error);
            // If we have cached recommendations, use them as fallback
            if (cachedRecommendations) {
                updateRecommendationCards(cachedRecommendations);
            }
        }
    } catch (error) {
        console.error('Error:', error);
        // If we have cached recommendations, use them as fallback
        if (cachedRecommendations) {
            updateRecommendationCards(cachedRecommendations);
        }
    } finally {
        isUpdating = false;
    }
}

function updateRecommendationCards(recommendations) {
    const cards = document.querySelectorAll('.choice-card, .choice-card1, .choice-card2');
    recommendations.forEach((song, index) => {
        if (cards[index]) {
            const card = cards[index];
            card.querySelector('.card-image').src = song.image;
            card.querySelector('.song-title').textContent = song.title;
            card.querySelector('.artist-name').textContent = song.artist;
            card.querySelector('.detail-item:nth-child(1) .detail-value').textContent = song.bpm;
            card.querySelector('.detail-item:nth-child(2) .detail-value').textContent = song.key || 'N/A';
            card.querySelector('.detail-item:nth-child(3) .detail-value').textContent = song.duration || 'N/A';
            
            // Format energy as percentage
            const energyValue = parseFloat(song.energy);
            const energyLevel = card.querySelector('.detail-item:nth-child(4) .detail-value');
            if (energyLevel && !isNaN(energyValue)) {
                energyLevel.textContent = `${Math.round(energyValue * 100)}%`;
            } else {
                energyLevel.textContent = 'N/A';
            }
        }
    });
}