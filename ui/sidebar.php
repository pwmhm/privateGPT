<?php
        session_start();
?>
<html>

<head>
    <style>
    button{
        font-family:Helvetica, Arial, Verdana;
        font-weight:bold;
        background: none;
        border:none;
        padding-bottom:10px;
    }
    .session {
        background: #8D918D;
        font: 1.5em Helvetica;
        border-radius: 10px;
        width:100%;
        padding-left:10px;
    }
    .title{
        width:70%;
        text-align:center;
    }
    .options{
        padding-top:10px;
        width:25%;
        text-align:center;
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
        echo "<div class='session' style='text-align:center'><p><button onclick=\"javascript:msg('new_sess', 'sess_".(count($rowcount) + 1)."')\">New Session</button></p></div>";

        foreach($rowcount as $row){
            echo "<div class='session'>
                        <p ><button class='title' style='display:inline-block;'onclick=\"javascript:get_hist('".$row['name']."')\">".$row['name']."</button>
                        <button class='options' style='display:inline-block;float:right;' onclick=\"javascript:delete_sess('".$row['name']."')\">X</button></p>
                 </div>";
        }
        echo "<br></br>";
        $myPDO = new PDO('sqlite:db/manager.db');
        $result = $myPDO->query("SELECT * FROM docs");
        foreach($result as $row){
            $name = explode("/", $row['doc_path']);
            $clean = str_replace("'", '', $name);
            print "<p>" . $row['id'] . ". <button class='title' style='display:inline-block; onclick=".$row['doc_path'].">".end($clean)."</button><button onclick=\"javascript:msg('deletion', ". $row['doc_path'].", 'docs')\">X</button></p>";
        }
        ?>
</body>

</html>