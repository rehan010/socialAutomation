// chart 4


var ctx5 = document.getElementById("followers-chart-line").getContext("2d");

var gradientStroke1 = ctx2.createLinearGradient(0, 230, 0, 50);

gradientStroke1.addColorStop(1, "rgb(70,130,180)");
gradientStroke1.addColorStop(0.2, "rgba(72,72,176,0.0)");
gradientStroke1.addColorStop(0, "rgb(100,149,237)"); //purple colors

var gradientStroke2 = ctx2.createLinearGradient(0, 230, 0, 50);

gradientStroke2.addColorStop(1, "rgb(135,206,250)");
gradientStroke2.addColorStop(0.2, "rgb(0,191,255)");
gradientStroke2.addColorStop(0, "rgba(20,23,0,0)"); //blue colors

var gradientStroke3 = ctx2.createLinearGradient(0, 230, 0, 50);

gradientStroke3.addColorStop(1, "rgb(219,112,147)");
gradientStroke3.addColorStop(0.2, "rgb(221,160,221)");
gradientStroke3.addColorStop(0, "rgb(199,21,133)");

var gradientStroke4 = ctx4.createLinearGradient(0, 230, 0, 50);

gradientStroke4.addColorStop(1, "rgba(255, 255, 0, 0.2)"); // Yellowish color with 20% opacity
gradientStroke4.addColorStop(0.2, "rgba(72, 72, 176, 0.0)");
gradientStroke4.addColorStop(0, "rgba(20, 23, 39, 0)"); // Transparent

let chart5;
async function fetchFollowersGraph(start = getFormattedDate(2) , end = getFormattedDate()) {
    const json = {
        'start': start,
        'end': end
    };

    const csrfToken = getCSRFToken();

    try {
        // Use fetch to send a POST request and await the response
        const response = await fetch("FollowersGraphApiview/", {
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
        var linkedInFollowersCounts = data['linkedin'];
        var facebookFollowersCounts = data['facebook'];
        var instagramFollowersCounts = data['instagram'];
        var googleFollowersCounts = data['google'];
        var dateLabels = data['labels'];

        if(chart5){
            chart5.destroy();
        }


        chart5 = new Chart(ctx5, {
        type: "line",
        data: {
        labels: dateLabels,
        datasets: [
          {
            label: "Linkedin",
            data: linkedInFollowersCounts,

            tension: 0.4,
            borderWidth: 3,
            pointRadius: 4,
            borderColor: "#1B5583",
            backgroundColor: gradientStroke1,
            fill: true,
            maxBarThickness: 6,
            pointBackgroundColor: "#6F8FAF",
            pointBorderColor: "#4682B4	",
          },
          {
            label: "Facebook",
            data: facebookFollowersCounts,

            borderColor: "#1877F2",
            borderWidth: 3,
            maxBarThickness: 6,
            lineTension: 0.3,
            backgroundColor: "#F0F8FF",
            fill: true,
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
            data: instagramFollowersCounts,

            borderWidth: 3,
            maxBarThickness: 6,
            lineTension: 0.3,
            backgroundColor: "#C13584",
            borderColor: "#FF8C00",
            fill: true,
            pointRadius: 4,
            pointBackgroundColor: "#C13584",
            pointBorderColor: "#E1306C",
            pointHoverBackgroundColor: "#E1306C",
          },
          {
            label: "Google",
            data: googleFollowersCounts,

            tension: 0,
            borderWidth: 0,
            pointRadius: 4,
            borderColor: "#F4B400",
            borderWidth: 3,
            backgroundColor: gradientStroke3,
            fill: true,

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
fetchFollowersGraph();





// end chart 3
