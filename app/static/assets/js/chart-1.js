// chart 1

var ctx = document.getElementById("chart-bars").getContext("2d");

new Chart(ctx, {
  type: "bar",
    data: {
    labels: labels, // Use the labels from your context
    datasets: [
      {
        label: "Linkedin Posts",
        tension: 0.4,
        borderWidth: 0,
        borderRadius: 4,
        borderSkipped: false,
        backgroundColor: "#0077B5",
        data: data_ln, // Use the data from your context
        maxBarThickness: 6,
      },
      {
        label: "Facebook Posts",
        tension: 0.4,
        borderWidth: 0,
        borderRadius: 4,
        borderSkipped: false,
        backgroundColor: "#1877F2",
        data: data_fb, // Use the data from your context
        maxBarThickness: 6,
      },
      {
        label: "Instagram Posts",
        tension: 0.4,
        borderWidth: 0,
        borderRadius: 4,
        borderSkipped: false,
        backgroundColor: "#C6011F",
        data: data_insta, // Use the data from your context
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
            size: 12,
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
          display: true,
          color: "#b2b9bf",
          padding: 15,
          font: {
            size: 12,
            family: "Open Sans",
            style: "normal",
            lineHeight: 2,
          },
          color: "#fff",
        },
      },
    },
  },
});

// end chart 1
