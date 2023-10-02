// chart 3


var ctx3 = document.getElementById("like-chart-line").getContext("2d");



var gradientStroke1 = ctx3.createLinearGradient(0, 230, 0, 50);

gradientStroke1.addColorStop(1, "rgb(70,130,180)");
gradientStroke1.addColorStop(0.2, "rgba(72,72,176,0.0)");
gradientStroke1.addColorStop(0, "rgb(100,149,237)"); //purple colors


var gradientStroke2 = ctx3.createLinearGradient(0, 230, 0, 50);


gradientStroke2.addColorStop(0, "rgba(59, 89, 152, 0.4)"); // Facebook Blue
gradientStroke2.addColorStop(1, "rgba(0, 0, 0, 0)");
gradientStroke2.addColorStop(0, "rgba(0, 119, 181, 0)");// Transparent

var gradientStroke3 = ctx3.createLinearGradient(0, 230, 0, 50);

gradientStroke3.addColorStop(1, "rgba(203,12,159,0.2)");
gradientStroke3.addColorStop(0.2, "rgba(72,72,176,0.0)");
gradientStroke3.addColorStop(0, "rgba(203,12,159,0)"); //purple colors


gradientStroke3.addColorStop(1, "rgb(219,112,147)");
gradientStroke3.addColorStop(0.2, "rgb(221,160,221)");
gradientStroke3.addColorStop(0, "rgb(199,21,133)");

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
            data: linkedInLikesCounts,

            tension: 0.4,
            borderWidth: 3,
            pointRadius: 4,
            borderColor: "#1B5583",

            fill: true,
            maxBarThickness: 6,
            pointBackgroundColor: "#6F8FAF",
            pointBorderColor: "#4682B4	",
          },
          {
            label: "Facebook",
            data: facebookLikesCounts,

            borderColor: "#1877F2",
            borderWidth: 3,
            maxBarThickness: 6,
            lineTension: 0.3,

            fill: false,
            pointRadius: 4,
            pointBackgroundColor: "#0096FF",
            pointBorderColor: "#1877F2",
            pointHoverRadius: 5,
            pointHoverBackgroundColor: "#1877F2",
            pointHitRadius: 50,
            pointBorderWidth: 2,
          },
          {
            label: "Instagram",
            data: instagramLikesCounts,

            borderWidth: 3,
            maxBarThickness: 6,
            lineTension: 0.3,


            borderColor: "#C13584",
            fill: false,
            pointRadius: 4,
            pointBackgroundColor: "red",
            pointBorderColor: "#E1306C",
            pointHoverBackgroundColor: "#E1306C",
          },
          {
            label: "Google",
            data: googleLikeCounts,

            tension: 0,
            borderWidth: 0,
            pointRadius: 3,
            borderColor: "#F4B400",
            borderWidth: 4,

            fill: false,

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
              mode: 'index',    // Set the mode to 'index'
              intersect: false,
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
            tooltips: {
              mode: 'index',    // Set the mode to 'index'
              intersect: false,
            },
            hover: {
              mode: 'index',    // Set the mode to 'index'
              intersect: false,
            },
          },
    });



    } catch (error) {
        // Handle any errors that occurred during the fetch
        console.error('Fetch error:', error);
    }


}






// end chart 3
