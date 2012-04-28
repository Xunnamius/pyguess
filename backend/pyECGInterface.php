<?php
	//Hello, python!
	if(isset($_POST['python'], $_POST['type'], $_POST['u'], $_POST['p']) && $_POST['python'] == 1)
	{
		//Some house cleaning
		header('Content-Type: text/plain');
		ini_set('session.use_cookies', 0);
		ini_set('session.use_trans_sid', 1);
		
		if(!filter_var($_SERVER['REMOTE_ADDR'], FILTER_VALIDATE_IP))
		{
			header("HTTP/1.0 404 Not Found");
			echo 'BadRequest';
			exit;
		}
		
		else $IP = $_SERVER['REMOTE_ADDR'];
		
		session_id(filter_var($_POST['SID'], FILTER_SANITIZE_STRING));
		session_start();
		
		//Maintenance mode (server offline when true)
		if($_SESSION['MAINTENANCE_MODE'])
		{
			echo 'MAINTENANCE_MODE';
			return;
		}
		
		//If they're sending a heartbeat packet
		if($_POST['type'] == 'bet' && $_POST['u'] == $_SESSION['u'] && $_POST['p'] == $_SESSION['p'])
		{
			//bump-bump (imagine a heartbeat, people)
			$dbc = mysqli_connect('mhousepython.db.4619325.hostedresource.com', '[REMOVED]', '[REMOVED]', '[REMOVED]');
			$row = mysqli_fetch_array(mysqli_query($dbc, 'SELECT username, connected FROM `users` WHERE SHA1(CONCAT(\''.substr($_SESSION['PYTHON']['challenge'], 0, 20).'\', username, \''.substr($_SESSION['PYTHON']['challenge'], 20, 20).'\')) = \''.$_POST['u'].'\' AND SHA1(CONCAT(\''.substr($_SESSION['PYTHON']['challenge'], 0, 20).'\', password, \''.substr($_SESSION['PYTHON']['challenge'], 20, 20).'\')) = \''.$_POST['p'].'\' LIMIT 1'));
			
			if($row['connected'] == 'T')
			{
				mysqli_query($dbc, "UPDATE users SET ECG_DATETIME = '".gmdate("Y-m-d H:i:s", time())."' WHERE username = '$row[username]' LIMIT 1");
				echo 'Okay';
			}
			
			else echo 'Die';
			mysqli_close($dbc);
			exit;
		}
		
		die('EndOfLegalScript');
	}
	
	header('Location: http://dignityice.com/dg/Xunnamius/house/pyLoginInterface.php');
?>