<?php
    $myPDO = new PDO('sqlite:db/manager.db');
    $result = $myPDO->query("SELECT * FROM docs");
    foreach($result as $row){
        print "<p>" . $row['id'] . "<a href=".$row['doc_path'].">".$row['doc_path']."</a>" . "</p>";
    }
?>