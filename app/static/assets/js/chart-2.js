// chart 2

var ctx2 = document.getElementById("chart-line").getContext("2d");

var gradientStroke1 = ctx2.createLinearGradient(0, 230, 0, 50);

gradientStroke1.addColorStop(1, "rgb(173, 216, 230)"); // Light Sky Blue
gradientStroke1.addColorStop(0.8, "rgba(255, 255, 0, 0)"); // Fully Transparent
gradientStroke1.addColorStop(0, "rgba(255, 255, 0, 0)"); // Fully Transparent

var gradientStroke2 = ctx2.createLinearGradient(0, 230, 0, 50);

gradientStroke2.addColorStop(1, "rgb(135,206,250)");
gradientStroke2.addColorStop(0.2, "rgb(0,191,255)");
gradientStroke2.addColorStop(0, "rgba(20,23,0,0)"); //blue colors

var gradientStroke3 = ctx2.createLinearGradient(0, 230, 0, 50);

gradientStroke3.addColorStop(1, "rgb(219,112,147)");
gradientStroke3.addColorStop(0.2, "rgb(221,160,221)");
gradientStroke3.addColorStop(0, "rgb(199,21,133)");

var gradient = ctx2.createLinearGradient(0, 0, 0, 450);
gradient.addColorStop(0, 'rgba(131,58,180,1)');
gradient.addColorStop(0.5, 'rgba(253,29,29,1)');
gradient.addColorStop(1, 'rgba(252,176,69,1)');

let chart2;
async function fetchPostGraph(start = getFormattedDate(2) , end = getFormattedDate()) {
    const json = {
        'start': `${start}`,
        'end': `${end}`
    };


    const csrfToken = getCSRFToken();

    try {
        // Use fetch to send a POST request and await the response
        const response = await fetch("PostGraphApiview/", {
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
        var linkedInCounts = data['linkedin'];
        var facebookCounts = data['facebook'];
        var instagramCounts = data['instagram'];
        var googleLikeCounts = data['google'];
        var labels = data['labels'];

        if(chart2){
            chart2.destroy();

        }


        chart2 = new Chart(ctx2, {
          type: "line",
          data: {
            labels: labels,
            datasets: [
              {
                label: "Linkedin",
                data: linkedInCounts,

                tension: 0.4,
                borderWidth: 3,
                pointRadius: 4,
                borderColor: "#1B5583",

                fill: false,
                maxBarThickness: 6,
                pointBackgroundColor: "#6F8FAF",
                pointBorderColor: "#4682B4	",
              },
              {
                label: "Facebook",
                data: facebookCounts,

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
                data: instagramCounts,


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
            tooltips: {
              mode: 'index',
              intersect: false,
              callbacks: {
                label: function (tooltipItem, data) {
                  var label = data.datasets[tooltipItem.datasetIndex].label || '';
                  var value = data.datasets[tooltipItem.datasetIndex].data[tooltipItem.index];
                  return label + ': ' + value;
                },
                title: function (tooltipItems, data) {
                  // Customize the title if needed
                  return 'Data at Time ' + data.labels[tooltipItems[0].index];
                },
              },
            },

            legend: {
                display: false,
            }
          },
        });
     } catch (error) {
        // Handle any errors that occurred during the fetch
        console.error('Fetch error:', error);
    }


}
fetchPostGraph();


// end chart 2
