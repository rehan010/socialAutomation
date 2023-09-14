// chart 3


var ctx3 = document.getElementById("like-chart-line").getContext("2d");

var gradientStroke1 = ctx3.createLinearGradient(0, 230, 0, 50);

gradientStroke1.addColorStop(1, "rgba(203,12,159,0.2)");
gradientStroke1.addColorStop(0.2, "rgba(72,72,176,0.0)");
gradientStroke1.addColorStop(0, "rgba(203,12,159,0)"); //purple colors

var gradientStroke2 = ctx3.createLinearGradient(0, 230, 0, 50);

gradientStroke2.addColorStop(1, "rgba(0, 0, 255, 0.2)");
gradientStroke2.addColorStop(0.2, "rgba(72,72,176,0.0)");
gradientStroke2.addColorStop(0, "rgba(20,23,39,0)"); //blue colors

var gradientStroke3 = ctx3.createLinearGradient(0, 230, 0, 50);

gradientStroke3.addColorStop(1, "rgba(255, 255, 0, 0.2)"); // Yellowish color with 20% opacity
gradientStroke3.addColorStop(0.2, "rgba(72, 72, 176, 0.0)");
gradientStroke3.addColorStop(0, "rgba(20, 23, 39, 0)"); // Transparent

var gradientStroke4 = ctx3.createLinearGradient(0, 230, 0, 50);

gradientStroke4.addColorStop(1, "rgba(255, 255, 0, 0.2)"); // Yellowish color with 20% opacity
gradientStroke4.addColorStop(0.2, "rgba(72, 72, 176, 0.0)");
gradientStroke4.addColorStop(0, "rgba(20, 23, 39, 0)"); // Transparent
let chart3;
async function fetchLikeGraph(start = getFormattedDate(2) , end = getFormattedDate()) {
    const json = {
        'start': `${start}`,
        'end': `${end}`
    };


    const csrfToken = getCSRFToken();

    try {
        // Use fetch to send a POST request and await the response
        const response = await fetch("likeGraphApiview/", {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken,
            },
            body: JSON.stringify(json),
        });

        // Await the JSON parsing of the response
        const data = await response.json();

        // Handle the JSON data here
        var linkedInLikesCounts = data['linkedin'];
        var facebookLikesCounts = data['facebook'];
        var instagramLikesCounts = data['instagram'];
        var googleLikeCounts = data['google'];
        var dateLabels = data['labels'];

        if(chart3){
            chart3.destroy();

        }

        chart3 = new Chart(ctx3, {
        type: "line",
        data: {
        labels: dateLabels,
        datasets: [
          {
            label: "Linkedin",
            tension: 0,
            borderWidth: 0,
            pointRadius: 3,
            borderColor: "#cb0c9f",
            borderWidth: 3,
            backgroundColor: gradientStroke1,
            fill: true,
            data: linkedInLikesCounts,
            maxBarThickness: 6,
          },
          {
            label: "Facebook",
            tension: 0,
            borderWidth: 0,
            pointRadius: 3,
            borderColor: "#1E90FF",
            borderWidth: 3,
            backgroundColor: gradientStroke2,
            fill: true,
            data: facebookLikesCounts,
            maxBarThickness: 6,
          },
          {
            label: "Instagram",
            tension: 0,
            borderWidth: 0,
            pointRadius: 3,
            borderColor: "#C6011F",
            borderWidth: 3,
            backgroundColor: gradientStroke3,
            fill: true,
            data: instagramLikesCounts,
            maxBarThickness: 6,
          },
          {
            label: "Google",
            tension: 0,
            borderWidth: 0,
            pointRadius: 3,
            borderColor: "#F4B400",
            borderWidth: 3,
            backgroundColor: gradientStroke3,
            fill: true,
            data: googleLikeCounts,
            maxBarThickness: 6,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: false,
          },
        },
        interaction: {
          intersect: false,
          mode: "nearest",
        },
        scales: {
          y: {
            grid: {
              drawBorder: false,
              display: true,
              drawOnChartArea: true,
              drawTicks: false,
              borderDash: [5, 5],
            },
            ticks: {
              display: true,
              padding: 10,
              color: "#b2b9bf",
              font: {
                size: 11,
                family: "Open Sans",
                style: "normal",
                lineHeight: 2,
              },
            },
          },
          x: {
            grid: {
              drawBorder: false,
              display: false,
              drawOnChartArea: false,
              drawTicks: false,
              borderDash: [5, 5],
            },
            ticks: {
              display: true,
              color: "#b2b9bf",
              padding: 20,
              font: {
                size: 11,
                family: "Open Sans",
                style: "normal",
                lineHeight: 2,
              },
            },
          },
        },
      },
    });



    } catch (error) {
        // Handle any errors that occurred during the fetch
        console.error('Fetch error:', error);
    }


}
fetchLikeGraph();





// end chart 3
