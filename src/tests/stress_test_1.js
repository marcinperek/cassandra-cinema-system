const autocannon = require("autocannon");

const result = autocannon(
  {
    url: "http://localhost:8888",
    connections: 10,
    duration: 30,
    requests: [
      {
        method: "GET",
        path: "/",
      },
    ],
  },
  (err, result) => {
    if (err) {
      console.error("Error:", err);
      process.exit(1);
    }
  }
);

autocannon.track(result);