var socket = io();
var nameForm = document.getElementById("name-form");
var messageInput = document.getElementById("message-input");
var sendButton = document.getElementById("send-button");

function addMessage(name, msg) {
  var chatbox = document.getElementById("chatbox");
  var messageElement = document.createElement("p");
  messageElement.textContent = name + ": " + msg;
  chatbox.appendChild(messageElement);
  chatbox.scrollTop = chatbox.scrollHeight;
}

sendButton.addEventListener("click", sendMessage);
messageInput.addEventListener("keypress", function (event) {
  if (event.key === "Enter") {
    sendMessage();
  }
});

document.getElementById("set-name-button").addEventListener("click", setName);
document
  .getElementById("name-input")
  .addEventListener("keydown", function (event) {
    if (event.key === "Enter") {
      setName();
    }
  });
var clientNAme = "";

function setName() {
  var name = document.getElementById("name-input").value;
  if (name.trim() !== "") {
    socket.emit("set_name", name);
    clientNAme = name;
    document.getElementById("name-form").style.display = "none";
    document.getElementById("sendbox").style.display = "block";
  }
}

function sendMessage() {
  var messageInput = document.getElementById("message-input");
  var message = messageInput.value;
  if (message.trim() !== "") {
    socket.emit("message", message);
    messageInput.value = "";
  }
}

// Helper: assign a color role based on name or IP, ensuring each user gets a unique color
const userRoleMap = {};
const userRoleColors = [
  { color: "#5865F2", class: "role-purple" }, // Discord blurple
  { color: "#ED4245", class: "role-red" }, // Discord red
  { color: "#57F287", class: "role-green" }, // Discord green
  { color: "#FAA61A", class: "role-yellow" }, // Discord yellow
  { color: "#EB459E", class: "role-pink" }, // Discord pink
  { color: "#00B0F4", class: "role-cyan" }, // Discord cyan
];
function getUserRole(name, ip) {
  if (name === "System") return { color: "", class: "system" };
  const key = name + ip;
  if (!userRoleMap[key]) {
    // Assign next available color
    const used = Object.values(userRoleMap).map((r) => r.class);
    const available = userRoleColors.filter((r) => !used.includes(r.class));
    userRoleMap[key] = available.length
      ? available[0]
      : userRoleColors[Object.keys(userRoleMap).length % userRoleColors.length];
  }
  return userRoleMap[key];
}

socket.on("message", (data) => {
  const messagesDiv = document.getElementById("messages");
  const newMessage = document.createElement("div");
  newMessage.classList.add("message");
  // System message detection
  let isSystem = data.name === "System";
  if (isSystem) {
    newMessage.classList.add("system");
  } else if (data.name.split(" ")[0] === clientNAme) {
    newMessage.classList.add("clientmsg");
  } else {
    newMessage.classList.add("user");
  }

  // Extract name and IP
  let namePart = data.name;
  let ipPart = "";
  const match = data.name.match(/^(.*?) \((.*?)\)$/);
  if (match) {
    namePart = match[1];
    ipPart = match[2];
  }
  const role = isSystem
    ? { color: "", class: "system" }
    : getUserRole(namePart, ipPart);
  // Render name and IP with color and larger font
  let nameHtml = "";
  let ipHtml = "";
  if (isSystem) {
    nameHtml = `<span class=\"name-role system\" style=\"font-family: 'Bookman Old Style', Bookman, serif; font-size:1em;font-weight:700;\">System</span>`;
  } else {
    nameHtml = `<span class=\"name-role ${role.class}\" style=\"font-size:1em;font-weight:600;color:${role.color}\">${namePart}</span>`;
    ipHtml = ipPart
      ? `<span class=\"ip-role\" style=\"font-size:0.95em;color:${role.color};opacity:0.7;\"> (${ipPart})</span>`
      : "";
  }
  const metaHtml = `<span class=\"meta-block\">${nameHtml}${ipHtml}${
    isSystem ? "" : ":"
  }</span>`;
  newMessage.innerHTML = `${metaHtml} <span class=\"msg-text\">${data.msg}</span>`;
  messagesDiv.appendChild(newMessage);
  messagesDiv.scrollTop = messagesDiv.scrollHeight;
});

socket.on("connect", function () {
  console.log("Connected to server");
});
