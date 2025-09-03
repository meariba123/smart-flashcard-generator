fetch("/get_progress")
  .then(res => res.json())
  .then(data => {
    new Chart(document.getElementById("progressChart"), {
      type: "bar",
      data: {
        labels: data.sets,
        datasets: [{
          label: "Accuracy (%)",
          data: data.accuracy,
          backgroundColor: data.accuracy.map(pct =>
            pct >= 70 ? "green" : pct >= 40 ? "orange" : "red"
          )
        }]
      },
      options: {
        scales: {
          y: { beginAtZero: true, max: 100 }
        }
      }
    });
  });
