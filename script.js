async function submitSong() {
    const title = document.getElementById("title").value;
    const artist = document.getElementById("artist").value;

    console.log("Sending data:", title, artist);  // Debugging log

    const response = await fetch("/vibe", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title, artist })
    });

    const result = await response.json();
    console.log("Response:", result);
}