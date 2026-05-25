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

  console.log(`Screening: ${screening.title} (${screeningId})`);
  console.log(`Total seats: ${totalSeats}`);

  const buildRequests = (email, name) => {
    let counter = 0;
    return [
      {
        method: "POST",
        path: "/",
        setupRequest(req) {
          const seat = counter++ % totalSeats;
          req.path = `/?user_email=${encodeURIComponent(email)}&user_name=${encodeURIComponent(name)}&screening_id=${screeningId}&seat_number=${seat}`;
          return req;
        },
      },
    ];
  };

  const requestsA = buildRequests("userA@test.com", "User A");
  const requestsB = buildRequests("userB@test.com", "User B");

  const runClient = (title, requests) =>
    new Promise((resolve) => {
      const inst = autocannon(
        {
          title,
          url: "http://localhost:8888",
          connections: totalSeats,
          amount: totalSeats,
          requests,
        },
        (err, result) => {
          if (err) {
            console.error(`${title} error:`, err);
            resolve(null);
          } else {
            resolve(result);
          }
        },
      );
      autocannon.track(inst, { renderProgressBar: title === "User A" });
    });

  const [resultA, resultB] = await Promise.all([
    runClient("User A", requestsA),
    runClient("User B", requestsB),
  ]);

  try {
    const data = await fetchJSON(
      `http://localhost:8888/?screening_id=${screeningId}`,
    );
    const reservations = data.movie_reservations ?? [];
    const byUser = {};
    for (const r of reservations) {
      byUser[r.user_name] = (byUser[r.user_name] ?? 0) + 1;
    }

    console.log(`Total seats booked: ${reservations.length} / ${totalSeats}`);
    let winner = null;
    let topCount = -1;
    for (const [name, count] of Object.entries(byUser)) {
      console.log(`  ${name}: ${count} seat(s)`);
      if (count > topCount) {
        topCount = count;
        winner = name;
      }
    }
  } catch (e) {
    console.log("Could not verify reservations:", e.message);
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
