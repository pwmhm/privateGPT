<?php
    session_start();
    $cur_active_chat = $_SESSION['active_session'];
    $myPDO = new PDO('sqlite:db/sessions.db');
    $result = $myPDO->query("SELECT * FROM ". $cur_active_chat);

    foreach($result as $row){
        $align = ($row['USER'] == 'AI' ? "left" : "right");

        print "<p align=".$align."><b>".$row['USER']."</b> : ".$row['MESSAGE']."</p>";
    }

?>