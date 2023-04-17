document.addEventListener("DOMContentLoaded", function () {
  const summarizeBtn = document.getElementById("summarize-btn");
  const summaryLengthSelect = document.getElementById("summary-length");

  summarizeBtn.addEventListener("click", function () {
    chrome.tabs.query({ active: true, currentWindow: true }, function (tabs) {
      const activeTab = tabs[0];
      const videoUrl = activeTab.url;
      const summaryLength = summaryLengthSelect.value;

      fetch("https://ytrecap.com/getNewLengthSummary", {
        method: "POST",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
        },
        body: `url=${encodeURIComponent(
          videoUrl
        )}&summary_length=${encodeURIComponent(summaryLength)}`,
      })
        .then((response) => {
          if (response.ok) {
            return response.json();
          } else {
            throw new Error("Network response was not ok");
          }
        })
        .then((data) => {
          const summary = data.summary;
          alert("Summary: " + summary);
        })
        .catch((error) => {
          console.error("There was a problem with the fetch operation:", error);
        });
    });
  });
});
