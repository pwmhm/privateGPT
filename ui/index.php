<?php
  session_start();
  $_SESSION['active_session'] = "sess_0";
?>
<!DOCTYPE html>
<html>
<head>
  <script src="jquery.min.js"></script>
  <script>
    function create_paragraph(class_name, content){
      const paragraph = document.createElement("p");
      const node = document.createTextNode(content);
      paragraph.appendChild(node)
      const target = document.getElementById(class_name)
      target.appendChild(paragraph)
    }
    
    function msg() {
        const res_body = JSON.stringify({ "request_type": "prompt", "content": "what happened to the patek?"})
        fetch("http://localhost:8000", {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: res_body
        })
        .then(response => response.json())
        .then(response => create_paragraph("res", response["content"])
        )
    }
  </script>
  <style>
    .history{
      width:20em;
      height:20em;
      border: 2px solid black;
      padding-left:1em;
      padding-right:1em;
    }
  </style>
</head>
<body>

<div class="main">
  <div class="sessions">
    <script>
      $(".sessions").load('sessions.php');
    </script>
  </div>
  <div class="history", id="chat">
    <script>
      $("#chat").load('chat.php');
    </script>
  </div>
  <div class="prompter">
    
  </div>
</div>

<h1>Chat with an AI</h1>
<div id="history">

</div>
<p>The button below activates a JavaScript when it is clicked.</p>
<form>
  <input type="text" id="lname", name="lname">
  <input type="button" value="Click me" onclick="msg()">
</form>

</body>
</html>
