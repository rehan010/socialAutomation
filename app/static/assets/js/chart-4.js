// chart 4


var ctx4 = document.getElementById("comments-chart-line").getContext("2d");


var gradientStroke1 = ctx4.createLinearGradient(0, 230, 0, 50);

gradientStroke1.addColorStop(1, "rgb(70,130,180)");
gradientStroke1.addColorStop(0.2, "rgba(72,72,176,0.0)");
gradientStroke1.addColorStop(0, "rgb(100,149,237)"); //purple colors

var gradientStroke2 = ctx4.createLinearGradient(0, 230, 0, 50);

gradientStroke2.addColorStop(1, "rgb(135,206,250)");
gradientStroke2.addColorStop(0.2, "rgb(0,191,255)");
gradientStroke2.addColorStop(0, "rgba(20,23,0,0)"); //blue colors

var gradientStroke3 = ctx4.createLinearGradient(0, 230, 0, 50);

gradientStroke3.addColorStop(1, "rgb(219,112,147)");
gradientStroke3.addColorStop(0.2, "rgb(221,160,221)");
gradientStroke3.addColorStop(0, "rgb(199,21,133)");

var gradientStroke4 = ctx4.createLinearGradient(0, 230, 0, 50);

gradientStroke4.addColorStop(1, "rgba(255, 255, 0, 0.2)"); // Yellowish color with 20% opacity
gradientStroke4.addColorStop(0.2, "rgba(72, 72, 176, 0.0)");
gradientStroke4.addColorStop(0, "rgba(20, 23, 39, 0)"); // Transparent
let chart4;
async function fetchCommentsGraph(start = getFormattedDate(7) , end = getFormattedDate()) {
    const json = {
        'start': start,
        'end': end
    };

    const csrfToken = getCSRFToken();

    try {
        // Use fetch to send a POST request and await the response
        const response = await fetch("CommentGraphApiview/", {
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
        var linkedInCommentsCounts = data['linkedin'];
        var facebookCommentsCounts = data['facebook'];
        var instagramCommentsCounts = data['instagram'];
        var googleCommentsCounts = data['google'];
        var dateLabels = data['labels'];

        if(chart4){
            chart4.destroy();
        }


        chart4 = new Chart(ctx4, {
        type: "line",
        data: {
        labels: dateLabels,
        datasets: [
          {
            label: "Linkedin",
            data: linkedInCommentsCounts,


            tension: 0,
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
            data: facebookCommentsCounts,

            borderColor: "#1877F2",
            borderWidth: 3,
            maxBarThickness: 6,
            lineTension: 0,

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
            data: instagramCommentsCounts,

            borderWidth: 3,
            maxBarThickness: 6,
            lineTension: 0,


            borderColor: "#C13584",
            fill: false,
            pointRadius: 4,
            pointBackgroundColor: "red",
            pointBorderColor: "#E1306C",
            pointHoverBackgroundColor: "#E1306C",
          },
          {
            label: "Google",
            data: googleCommentsCounts,

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
                  drawBorder: true,
                  display: true,
                  drawOnChartArea: true,
                  drawTicks: false,

                },
                ticks: {
                  display: true,
                  padding: 10,
                  color: "#191970",
                  font: {
                    size: 9,
                    family: "Open Sans",
                    style: "normal",
                    lineHeight: 2,
                  },
                },
              },
              x: {
                grid: {
                  drawBorder: true,
                  display: false,
                  drawOnChartArea: false,
                  drawTicks: false,

                },
                ticks: {
                  display: true,
                  color: "#191970",
                  padding: 10,
                  font: {
                    size: 8,
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
    const fromDate = document.getElementById('from-date');
    const toDate = document.getElementById('to-date');
    fromDate.value = start;
    toDate.value = end;


}






// end chart 3
