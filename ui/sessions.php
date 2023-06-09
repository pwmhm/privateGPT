<?php
        session_start();
?>
<html>

<head>
    <style>
    .session {
        background: #8D918D;
        font: 1.5em Helvetica;
        border-radius: 10px;
        width:100%;
        padding-left:10px;
        text-align:center;
        align:center;
    }
    </style>
    <script>
    </script>
</head>

<body>
        
        <?php
        $myPDO = new PDO('sqlite:db/manager.db');
        $result = $myPDO->query("SELECT * FROM sqlite_master WHERE type='table' AND name LIKE 'sess_%'");
        $rowcount = $result->fetchAll();
        echo "<div class='session'><p><a href=\"javascript:msg('new_sess', 'sess_".(count($rowcount) + 1)."')\">New Session</a></p></div>";

        foreach($rowcount as $row){
            echo "<div class='session'><p ><a href=\"javascript:get_hist('".$row['name']."')\">".$row['name']."</a></p></div>";
        }
        ?>
</body>

</html>