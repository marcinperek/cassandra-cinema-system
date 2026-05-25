const autocannon = require("autocannon");
const http = require("http");

function fetchJSON(url) {
  return new Promise((resolve, reject) => {
    http
      .get(url, (res) => {
        let data = "";
        res.on("data", (chunk) => (data += chunk));
        res.on("end", () => {
          try {
            resolve(JSON.parse(data));
          } catch (e) {
            reject(new Error("Failed to parse JSON: " + data));
          }
        });
      })
      .on("error", reject);
  });
}

async function main() {
  const { movie_list } = await fetchJSON("http://localhost:8888/");
  if (!movie_list || movie_list.length === 0) {
    console.error("No movies found.");
    process.exit(1);
  }

  const screening = movie_list[0];
  const screeningId = screening.screening_id;
  const totalSeats = screening.total_seats;
  console.log(`Using screening: ${screening.title} (${screeningId}), total seats: ${totalSeats}\n`);

  const randomSeat = () => Math.floor(Math.random() * totalSeats);

  const requests = [
    { method: "GET", path: "/" },
    { method: "GET", path: `/?screening_id=${screeningId}` },
    { method: "GET", path: "/?user_email=alice%40test.com" },
    { method: "GET", path: "/?user_email=bob%40test.com" },
    {
      method: "POST",
      path: "/",
      setupRequest(req) {
        req.path = `/?user_email=alice%40test.com&user_name=Alice&screening_id=${screeningId}&seat_number=${randomSeat()}`;
        return req;
      },
    },
    {
      method: "POST",
      path: "/",
      setupRequest(req) {
        req.path = `/?user_email=bob%40test.com&user_name=Bob&screening_id=${screeningId}&seat_number=${randomSeat()}`;
        return req;
      },
    },
    {
      method: "POST",
      path: "/",
      setupRequest(req) {
        req.path = `/?user_email=carol%40test.com&user_name=Carol&screening_id=${screeningId}&seat_number=${randomSeat()}`;
        return req;
      },
    },
  ];

  const runClient = (title, connections) =>
    new Promise((resolve) => {
      const inst = autocannon(
        {
          title,
          url: "http://localhost:8888",
          connections,
          duration: 30,
          requests,
        },
        (err, result) => {
          if (err) {
            console.error(`${title} error:`, err);
            resolve(null);
          } else {
            resolve(result);
          }
        }
      );
      autocannon.track(inst, { renderProgressBar: title === "Client 1" });
    });

  const [r1, r2, r3] = await Promise.all([
    runClient("Client 1", 5),
    runClient("Client 2", 5),
    runClient("Client 3", 5),
  ]);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
