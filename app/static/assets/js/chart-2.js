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
async function fetchPostGraph(start = getFormattedDate(7) , end = getFormattedDate()) {

    // Create a new Date object to represent the current date and time
    const currentTime = new Date();

    // Extract the current hours, minutes, and seconds
    const hours = currentTime.getHours();
    const minutes = currentTime.getMinutes();
    const seconds = currentTime.getSeconds();

    // Format the time as a string (e.g., "hh:mm:ss")
    const formattedTime = `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;

//    start = start + " " + formattedTime;
//    end = end + " " + formattedTime;

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

                tension: 0,
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
                data: instagramCounts,


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
                data: googleLikeCounts,


                borderWidth: 3,
                maxBarThickness: 6,
                lineTension: 0,

                borderColor: "#F4B400",
                fill: false,
                pointRadius: 4,

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
                  stepSize: 1,
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


}


// end chart 2
