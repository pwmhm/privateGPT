<?php
    session_start();
?>
<html>
    <head>
    </head>
    <body>
        <?php
            $myPDO = new PDO('sqlite:db/manager.db');

            if( isset($_GET['sess']))
            {
                $selected_session = cleanInput($_GET['sess']);
                $result = $myPDO->query("SELECT * FROM $selected_session");
            
                foreach($result as $row){
                    $align = ($row['user'] == 'AI' ? "left" : "right");
                    print "<p align=".$align."><b>".$row['user']."</b> : ".$row['message']."</p>";
                }
            }
            function cleanInput($input){
                $clean = strtolower( $input); //string becomes lowercase
                // $clean = substr( $clean,0,12); //The string takes the first 12 digits, and the rest is discarded.
                $clean = str_replace("'", '', $clean);
                return $clean;
              }
        ?>
    </body>
</html>