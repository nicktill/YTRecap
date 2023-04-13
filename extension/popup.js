document.getElementById("summarize-btn").addEventListener("click", async () => {
  const summaryLength = document.getElementById("summary-length").value;

  chrome.tabs.query({ active: true, currentWindow: true }, async (tabs) => {
    console.log("Active tab queried:", tabs);
    try {
      const response = await new Promise((resolve) => {
        chrome.tabs.sendMessage(tabs[0].id, { action: "getVideoUrl" }, resolve);
      });

      console.log("Response received in popup.js:", response);
      if (response && response.url) {
        const videoUrl = response.url;

        // Send the video URL and summary length to the external app
        const appResponse = await fetch(
          `https://ytrecap.org?videoUrl=${encodeURIComponent(
            videoUrl
          )}&summaryLength=${summaryLength}`
        );
        const summary = await appResponse.text();

        // Display the received summary on the YouTube page
        chrome.scripting.executeScript(
          {
            target: { tabId: tabs[0].id },
            func: (summary) => {
              const summaryHtml = `
                    <div id="ytrecap-summary-container" style="position: fixed; bottom: 0; left: 0; right: 0; z-index: 99999; background-color: white; padding: 20px; border-top: 1px solid black; font-size: 16px;">
                      <h2>Summary</h2>
                      <p>${summary}</p>
                      <button id="ytrecap-close-btn" style="position: absolute; top: 10px; right: 10px;">Close</button>
                    </div>`;
              document.body.insertAdjacentHTML("beforeend", summaryHtml);
            },
            args: [summary],
          },
          () => {
            // Close the summary when the close button is clicked
            chrome.scripting.executeScript({
              target: { tabId: tabs[0].id },
              func: () => {
                document
                  .getElementById("ytrecap-close-btn")
                  .addEventListener("click", () => {
                    document
                      .getElementById("ytrecap-summary-container")
                      .remove();
                  });
              },
            });
          }
        );
      } else {
        console.log("Video URL not found");
      }
    } catch (error) {
      console.error("Error in popup.js:", error);
    }
  });
});
