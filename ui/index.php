<?php
  session_start();
?>
<!DOCTYPE html>
<html>
<head>
  <script src="jquery.min.js"></script>
  <script>
    let active_session = "";

    // TODO get_hist and refresh has a conflict. fix this.
    async function refresh(){
      if(active_session){
        $("#chat").load(`chat.php/?sess=${active_session}`);
      } else{
        $("#chat").load(`chat.php`);
      }
      $("#sess").load('sessions.php');
    }

    // function when changing active session, separate from refresh_chat()
    function get_hist(sess){
                active_session=sess;
            }
    
    // main function for sending requests
    function msg(req_type, content, session=""){
        const res_body = JSON.stringify({ "request_type": req_type, "content": content, "session": session})
        fetch("http://localhost:8000", {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: res_body
        })
      }

    // wrapper for sending prompt to gpt.
    function get_prompt(){
      const content = document.getElementById("prompt");
      msg("prompt", content.value, active_session);
    }

    function delete_sess(sess){
      if (active_session === sess){
        active_session = "";
      }
      msg("deletion", "", sess);
    }

    window.addEventListener('load', function(){
      setInterval(async function(){
          await refresh();
      }, 600);
    });
    
  </script>
  <style>
    html{
      height:98vh;
      width:auto;
      background: #4f5b66;
      font: 1em helvetica;
      z-index: 100;
    }
    body{
      height:inherit;
      width:inherit;
    }
    .main{
    display: inline-block;
    width:100%;
    height:100%;
    }
    .history{
      font-size: 1.8em;
      display:inherit;
      float:right;
      width:83.5%;
      height:75%;
      padding-left:1em;
      padding-right:1em;
      overflow-y: auto;
      z-index: -1;
    }
    .sessions{
      background:#343d46;
      display:inherit;
      width:12%;
      height:76%;
      padding-left:5px;
      padding-right:1em;
      margin-bottom:-25px;
    }
    .prompter{
      background:#343d46;
      display:block;
      width:auto;
      height:23%;
      padding-left:1em;
      padding-right:1em;
      z-index: 10;
    }
  </style>
</head>
<body>

<div class="main">
  <div class="sessions", id="sess">
    <script>
      $("#sess").load('sidebar.php');
    </script>
  </div>
  <div class="history", id="chat">
    <script>
      $("#chat").load('chat.php');
    </script>
  </div>
  <div class="prompter">
  <h1>Chat with an AI</h1>
  <p>The button below activates a JavaScript when it is clicked.</p>
  <form>
    <input type="text" id="prompt" onkeydown="return (event.keyCode!=13);">
    <input type="button" value="Click me" onclick="get_prompt()">
  </form>
  </div>
</div>

</body>
</html>
