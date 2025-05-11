import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from PIL import Image
import urllib.request
import io

# Example BPM and images
bpm_values = [120, 135, 110, 145]
image_paths = ['https://i.scdn.co/image/ab67616d00001e0259998815d706661e2c404d9f', 
               'https://i.scdn.co/image/ab67616d00001e02f72f1e38e9bd48f18a17ed9b', 
               'https://i.scdn.co/image/ab67616d00001e024b292ed7c7360a04d3d6b74a', 
               'https://i.scdn.co/image/ab67616d00001e02ba7fe7dd76cd4307e57dd75f']
labels = ['Song A', 'Song B', 'Song C', 'Song D']

fig, ax = plt.subplots(figsize=(10, 6))
x = list(range(len(bpm_values)))

# Set off-black background color
fig.patch.set_facecolor('#222222')  # Slightly off-black

# Plot the line with a neon effect
ax.plot(x, bpm_values, marker='o', linestyle='-', color='#00FF00', linewidth=3, markersize=10)  # Neon green

# Add images at each point with slight hand-drawn feel
for i, (xi, img_url) in enumerate(zip(x, image_paths)):
    img_data = urllib.request.urlopen(img_url).read()
    img = Image.open(io.BytesIO(img_data))
    imagebox = OffsetImage(img, zoom=0.18, resample=True)
    ab = AnnotationBbox(imagebox, (xi, bpm_values[i]), frameon=False)
    ax.add_artist(ab)

# Optional: Add labels under each image with neon colors and a hand-written font style
ax.set_xticks(x)
ax.set_xticklabels(labels, fontsize=12, rotation=45, fontweight='light', color='white')  # Changed to white for labels

# Styling
ax.set_ylabel("BPM", fontsize=14, color='white')
ax.set_title("BPM Across Tracks", fontsize=18, weight='bold', color='white')

# Remove gridlines (no orange lines anymore)
ax.grid(False)  # Disable gridlines

# Remove spines to add more artistic feel
for spine in ax.spines.values():
    spine.set_visible(False)

# Add some artsy details by adding some neon purple accents
ax.axhline(y=0, color='#800080', linewidth=2)  # Neon purple line at y=0

# Set the background to an off-black color to match the app’s theme
ax.set_facecolor('#222222')

# Show plot with some spacing around edges
plt.tight_layout(pad=4)
plt.show()
