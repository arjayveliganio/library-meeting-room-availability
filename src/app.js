const $ = (id) => document.getElementById(id);

function todayISO() {
  const d = new Date();
  const pad = (n) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}

async function loadAvailability() {
  const date = $("date").value;
  const res = await fetch(`/api/rooms?date=${encodeURIComponent(date)}`);
  const data = await res.json();

  const grid = $("grid");
  grid.innerHTML = "";

  data.rooms.forEach(r => {
    const div = document.createElement("div");
    div.className = "room";
    div.innerHTML = `<h3>${r.roomId}</h3>` + r.slots.map(s =>
      `<div class="slot ${s.status}">${s.slot} — ${s.status}</div>`
    ).join("");
    grid.appendChild(div);
  });
}

async function createBooking() {
  const payload = {
    date: $("date").value,
    roomId: $("room").value,
    slot: $("slot").value,
    name: $("name").value,
    email: $("email").value
  };

  const res = await fetch("/api/bookings", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });

  const text = await res.text();
  $("bookResult").textContent = `Status: ${res.status}\n${text}`;

  if (res.ok) {
    const doc = JSON.parse(text);
    $("bookingId").value = doc.id; 
    await loadAvailability();
  }
}

async function cancelBooking() {
  const id = $("bookingId").value.trim();
  const res = await fetch(`/api/bookings/${encodeURIComponent(id)}`, { method: "DELETE" });
  const text = await res.text();
  $("cancelResult").textContent = `Status: ${res.status}\n${text}`;
  if (res.ok) await loadAvailability();
}

$("date").value = todayISO();
$("load").onclick = loadAvailability;
$("book").onclick = createBooking;
$("cancel").onclick = cancelBooking;
loadAvailability();
