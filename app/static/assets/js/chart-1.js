// chart 1

var ctx = document.getElementById("chart-bars").getContext("2d");

new Chart(ctx, {
  type: "bar",
    data: {
    labels: labels, // Use the labels from your context
    datasets: [
      {
        label: "Posts",
        tension: 0.4,
        borderWidth: 0,
        borderRadius: 4,
        borderSkipped: false,
        backgroundColor: "#fff",
        data: data, // Use the data from your context
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
      mode: "index",
    },
    scales: {
      y: {
        grid: {
          drawBorder: false,
          display: false,
          drawOnChartArea: false,
          drawTicks: false,
        },
        ticks: {
          suggestedMin: 0,
          suggestedMax: 600,
          beginAtZero: true,
          padding: 15,
          font: {
            size: 14,
            family: "Open Sans",
            style: "normal",
            lineHeight: 2,
          },
          color: "#fff",
        },
      },
      x: {
        grid: {
          drawBorder: false,
          display: false,
          drawOnChartArea: false,
          drawTicks: false,
        },
        ticks: {
          display: false,
        },
      },
    },
  },
});

// end chart 1
