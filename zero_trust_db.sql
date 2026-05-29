-- MySQL dump 10.13  Distrib 8.0.45, for Win64 (x86_64)
--
-- Host: localhost    Database: zero_trust_db
-- ------------------------------------------------------
-- Server version	8.0.41

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `security_logs`
--

DROP TABLE IF EXISTS `security_logs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `security_logs` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int DEFAULT NULL,
  `username` varchar(100) DEFAULT NULL,
  `event_type` varchar(50) DEFAULT NULL,
  `action` varchar(100) DEFAULT NULL,
  `status` varchar(20) DEFAULT NULL,
  `ip_address` varchar(45) DEFAULT NULL,
  `user_agent` text,
  `details` text,
  `timestamp` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `fk_security_logs_user` (`user_id`),
  CONSTRAINT `fk_security_logs_user` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB AUTO_INCREMENT=33 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `security_logs`
--

LOCK TABLES `security_logs` WRITE;
/*!40000 ALTER TABLE `security_logs` DISABLE KEYS */;
INSERT INTO `security_logs` VALUES (2,NULL,'raheema5',NULL,'failed_login','failure','127.0.0.1','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36 Edg/146.0.0.0','Failed login for non-existent user from Localhost, Local Development','2026-04-07 19:24:40'),(3,1,'raheema5',NULL,'login','success','127.0.0.1','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36 Edg/146.0.0.0','Successful login from Localhost, Local Development','2026-04-07 19:24:50'),(6,6,'test',NULL,'login','success','127.0.0.1','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36 Edg/146.0.0.0','Successful login from Localhost, Local Development','2026-04-07 19:58:42'),(7,1,'raheema5',NULL,'login','success','127.0.0.1','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36 Edg/146.0.0.0','Successful login from Localhost, Local Development','2026-04-07 19:59:00'),(8,NULL,'root',NULL,'login','success','127.0.0.1','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36 Edg/146.0.0.0','Successful login from Localhost, Local Development','2026-04-07 19:59:52'),(9,NULL,'root',NULL,'failed_login','failure','127.0.0.1','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36 Edg/146.0.0.0','Failed login attempt from Localhost, Local Development','2026-04-07 20:00:52'),(10,NULL,'root',NULL,'login','success','127.0.0.1','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36 Edg/146.0.0.0','Successful login from Localhost, Local Development','2026-04-07 20:09:10'),(11,NULL,'root',NULL,'transfer_initiated','success','127.0.0.1','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36 Edg/146.0.0.0','Transfer of $450.00 - Risk Score: 30 - Ref: TX20260407JKNPLU5M','2026-04-07 20:10:59'),(12,NULL,'root',NULL,'unusual_time','warning','127.0.0.1','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36 Edg/146.0.0.0','Login at unusual time: 2:00','2026-04-08 00:40:02'),(13,NULL,'root',NULL,'login','success','127.0.0.1','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36 Edg/146.0.0.0','Successful login from Localhost, Local Development','2026-04-08 00:40:02'),(14,NULL,'\' OR \'1\'=\'1',NULL,'failed_login','failure','127.0.0.1','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36 Edg/146.0.0.0','Failed login for non-existent user from Localhost, Local Development','2026-04-08 00:44:35'),(15,NULL,'root',NULL,'login','success','127.0.0.1','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36 Edg/146.0.0.0','Successful login from Localhost, Local Development','2026-04-08 19:29:14'),(16,NULL,'root',NULL,'transfer_initiated','success','127.0.0.1','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36 Edg/146.0.0.0','Transfer of $3.00 - Risk Score: 25 - Ref: TX20260408T2LTM8L1','2026-04-08 19:29:47'),(17,NULL,'root',NULL,'transfer_initiated','success','127.0.0.1','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36 Edg/146.0.0.0','Transfer of $200.00 - Risk Score: 30 - Ref: TX20260413STPD2DZO','2026-04-13 07:58:51'),(18,NULL,'raheema5',NULL,'failed_login','failure','127.0.0.1','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36 Edg/146.0.0.0','Failed login for non-existent user from Localhost, Local Development','2026-04-13 08:00:45'),(19,NULL,'raheema5',NULL,'failed_login','failure','127.0.0.1','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36 Edg/146.0.0.0','Failed login for non-existent user from Localhost, Local Development','2026-04-13 08:00:57'),(20,20,'AR',NULL,'registration','success','127.0.0.1','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36 Edg/146.0.0.0','User registered from Localhost, Local Development with verified mobile +447301319668','2026-04-13 22:19:42'),(21,20,'AR',NULL,'unusual_time','warning','127.0.0.1','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36','Login at unusual time: 0:00','2026-04-13 22:34:27'),(22,20,'AR',NULL,'login','success','127.0.0.1','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36','Successful login from Localhost, Local Development','2026-04-13 22:34:27'),(23,20,'AR',NULL,'unusual_time','warning','127.0.0.1','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36 Edg/146.0.0.0','Login at unusual time: 1:00','2026-04-13 23:03:48'),(24,20,'AR',NULL,'login','success','127.0.0.1','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36 Edg/146.0.0.0','Successful login from Localhost, Local Development','2026-04-13 23:03:48'),(25,20,'AR',NULL,'failed_login','failure','127.0.0.1','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36 Edg/146.0.0.0','Failed login attempt from Localhost, Local Development','2026-04-13 23:05:36'),(26,20,'AR',NULL,'failed_login','failure','127.0.0.1','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36 Edg/146.0.0.0','Failed login attempt from Localhost, Local Development','2026-04-13 23:05:50'),(27,20,'AR',NULL,'unusual_time','warning','127.0.0.1','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36 Edg/146.0.0.0','Login at unusual time: 1:00','2026-04-13 23:06:03'),(28,20,'AR',NULL,'login','success','127.0.0.1','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36 Edg/146.0.0.0','Successful login from Localhost, Local Development','2026-04-13 23:06:03'),(29,20,'AR',NULL,'unusual_time','warning','127.0.0.1','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36 Edg/146.0.0.0','Login at unusual time: 1:00','2026-04-13 23:09:17'),(30,20,'AR',NULL,'login','success','127.0.0.1','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36 Edg/146.0.0.0','Successful login from Localhost, Local Development','2026-04-13 23:09:17'),(31,20,'AR',NULL,'login','success','127.0.0.1','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36 Edg/146.0.0.0','Successful login from Localhost, Local Development','2026-04-14 20:06:46'),(32,20,'AR',NULL,'transfer_initiated','success','127.0.0.1','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36 Edg/146.0.0.0','Transfer of $34.00 - Risk Score: 25 - Ref: TX20260414OJ1N428B','2026-04-14 20:08:56');
/*!40000 ALTER TABLE `security_logs` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `transactions`
--

DROP TABLE IF EXISTS `transactions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `transactions` (
  `id` int NOT NULL AUTO_INCREMENT,
  `from_user_id` int DEFAULT NULL,
  `to_user_id` int DEFAULT NULL,
  `amount` float NOT NULL,
  `type` varchar(50) DEFAULT NULL,
  `description` varchar(200) DEFAULT NULL,
  `status` varchar(50) DEFAULT 'pending',
  `reference_id` varchar(50) DEFAULT NULL,
  `ip_address` varchar(45) DEFAULT NULL,
  `location_city` varchar(100) DEFAULT NULL,
  `location_country` varchar(100) DEFAULT NULL,
  `risk_score` int DEFAULT '0',
  `approved_by` int DEFAULT NULL,
  `approved_at` datetime DEFAULT NULL,
  `notes` text,
  `timestamp` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `reference_id` (`reference_id`),
  KEY `from_user_id` (`from_user_id`),
  KEY `to_user_id` (`to_user_id`),
  KEY `approved_by` (`approved_by`),
  CONSTRAINT `transactions_ibfk_1` FOREIGN KEY (`from_user_id`) REFERENCES `user` (`id`) ON DELETE SET NULL,
  CONSTRAINT `transactions_ibfk_2` FOREIGN KEY (`to_user_id`) REFERENCES `user` (`id`) ON DELETE SET NULL,
  CONSTRAINT `transactions_ibfk_3` FOREIGN KEY (`approved_by`) REFERENCES `user` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `transactions`
--

LOCK TABLES `transactions` WRITE;
/*!40000 ALTER TABLE `transactions` DISABLE KEYS */;
INSERT INTO `transactions` VALUES (1,NULL,8,450,'transfer','Transfer to  Eve Frami','completed','TX20260407JKNPLU5M','127.0.0.1','Localhost','Local Development',30,NULL,NULL,NULL,'2026-04-07 21:10:59'),(2,NULL,14,3,'transfer','Transfer to chayan','completed','TX20260408T2LTM8L1','127.0.0.1','Localhost','Local Development',25,NULL,NULL,NULL,'2026-04-08 20:29:47'),(3,NULL,15,200,'transfer','Transfer to Legendarybrotherqk@gmail.com: enjoy ','completed','TX20260413STPD2DZO','127.0.0.1','Localhost','Local Development',30,NULL,NULL,NULL,'2026-04-13 08:58:51'),(4,20,6,34,'transfer','Transfer to test: enjoy ','completed','TX20260414OJ1N428B','127.0.0.1','Localhost','Local Development',25,NULL,NULL,NULL,'2026-04-14 21:08:56');
/*!40000 ALTER TABLE `transactions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `user`
--

DROP TABLE IF EXISTS `user`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `user` (
  `id` int NOT NULL AUTO_INCREMENT,
  `username` varchar(100) NOT NULL,
  `email` varchar(150) NOT NULL,
  `password_hash` varchar(200) NOT NULL,
  `role` varchar(50) DEFAULT NULL,
  `failed_attempts` int DEFAULT NULL,
  `is_locked` tinyint(1) DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `last_login` datetime DEFAULT NULL,
  `otp_secret` varchar(32) DEFAULT NULL,
  `is_otp_enabled` tinyint(1) DEFAULT NULL,
  `mobile` varchar(20) DEFAULT NULL,
  `is_mobile_verified` tinyint(1) DEFAULT '0',
  `mobile_otp` varchar(6) DEFAULT NULL,
  `mobile_otp_expiry` datetime DEFAULT NULL,
  `reset_token` varchar(100) DEFAULT NULL,
  `reset_token_expiry` datetime DEFAULT NULL,
  `email_verified` tinyint(1) DEFAULT '0',
  `email_verification_token` varchar(100) DEFAULT NULL,
  `email_verification_expiry` datetime DEFAULT NULL,
  `webauthn_credential_id` blob,
  `webauthn_public_key` blob,
  `webauthn_sign_count` int DEFAULT '0',
  `registration_ip` varchar(45) DEFAULT NULL,
  `registration_city` varchar(100) DEFAULT NULL,
  `registration_country` varchar(100) DEFAULT NULL,
  `registration_lat` float DEFAULT NULL,
  `registration_lon` float DEFAULT NULL,
  `last_login_ip` varchar(45) DEFAULT NULL,
  `last_login_city` varchar(100) DEFAULT NULL,
  `last_login_country` varchar(100) DEFAULT NULL,
  `last_login_lat` float DEFAULT NULL,
  `last_login_lon` float DEFAULT NULL,
  `known_ips` text,
  `balance` float DEFAULT '1000',
  `daily_transaction_total` float DEFAULT '0',
  `daily_transaction_date` date DEFAULT NULL,
  `monthly_transaction_total` float DEFAULT '0',
  `monthly_transaction_date` date DEFAULT NULL,
  `daily_limit` float DEFAULT '500',
  `monthly_limit` float DEFAULT '5000',
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`),
  UNIQUE KEY `email` (`email`)
) ENGINE=InnoDB AUTO_INCREMENT=21 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `user`
--

LOCK TABLES `user` WRITE;
/*!40000 ALTER TABLE `user` DISABLE KEYS */;
INSERT INTO `user` VALUES (1,'raheema5','chaudharyraheem025@gmail.com','$2b$12$6BLmabvNOCc5qjZggQAraOc.O9yHeAz.Blq2czXsR/310mjrFC8G.','admin',0,0,'2026-03-15 12:58:57','2026-04-07 20:59:15','JBSWY3DPEHPK3PXP',1,'+447301319668',0,NULL,'2026-03-17 23:51:37',NULL,NULL,1,NULL,NULL,_binary '˜òîLQ\rg\‡\”I%ñœ¥≥;(ß\‚\ ~Rz{¸%Ú§',_binary '•& !X \Ë)Gé\’}<õëR\À…ª(âù+f?Z\“^\≈√ú\Ê[\"X 0\Ô+i~\‰ù\Ó\‘f\÷\ŸUP\Î∑`¿\Â^ˆŸå+7D\·',42,NULL,NULL,NULL,NULL,NULL,'127.0.0.1','Localhost','Local Development',0,0,NULL,1006,0,'2026-03-26',0,'2026-03-26',500,5000),(3,'admin','abdulraheem87@gamil.com','$2b$12$gAUVjo4/1ulxdPG6bdpU0eS.Nl0rP.OGuFGmUgGWW0E7D7W3U.MjG','customer',1,1,'2026-03-15 14:35:20',NULL,NULL,0,NULL,0,NULL,NULL,NULL,NULL,0,'sUA8xWCrEXCWBJ1G10V9cE_Pg0sZe55Qef2HepsW6Zg','2026-03-16 14:35:21',NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,1000,0,'2026-03-26',0,'2026-03-26',500,5000),(4,'testuser2','test2@example.com','$2b$12$9AJW8//VD4OkBx1OnG/KY.16qzpEvfhC9RPBDUU5axdIRCe8GjJYO','customer',0,0,'2026-03-15 15:05:07','2026-03-15 15:09:27',NULL,0,NULL,0,NULL,NULL,NULL,NULL,1,NULL,NULL,NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,1000,0,'2026-03-26',0,'2026-03-26',500,5000),(5,'mj','abdulraheemg87@gmail.com','$2b$12$aBgPl4bPR/7C7G5thFTQsuNJgr1EIDJKEocdW8bRRk2XUyNnGqJaK','employee',1,0,'2026-03-17 00:53:32','2026-03-23 19:24:57','7BENSY635ZH3C23F2MYDV4VTGRFRM3GE',1,NULL,0,NULL,NULL,'OM60Xix-nSHGlkyfOLX1gl-KEeFoSaxyyJKNkRB9XWc','2026-04-14 01:04:30',1,'94gIaleqjzYnSHoynn8MgETWZF81kjUCFHRFArL7GBI','2026-03-18 00:53:33',_binary 'ˆò\◊Ü\’p\ÈÇ|zö',_binary '•& !X \ƒh•3O≤kj™¯ÆÄ(ÄΩ\»a˝ò0ì2%*\¬	zP\"X \⁄˜A¶æxÄw≤é\⁄CD?\–\ƒw\·\‹G)\Í>\ÕKZ59',0,NULL,'Tokyo','Japan',35.6762,139.65,NULL,'Tokyo','Japan',35.6762,139.65,NULL,1008,0,'2026-03-26',0,'2026-03-26',500,5000),(6,'test','abdulrahimmm575@gmail.com','$2b$12$gE2UbetRrttPnGODLxe9xO/JyB1PAeQDWfw2fODyKxINZ1vMguDlW','customer',0,0,'2026-03-23 23:13:15','2026-04-07 20:58:42','D2TX3YCZXOWO2PO5JZKNQSMPQPUN6CWT',0,'447301319668',0,'929669','2026-03-29 10:14:11',NULL,NULL,1,NULL,NULL,_binary '$ç~\÷14µ3\≈Y\"Q[ÜóûÜ\Í',_binary '•& !X M.	êê\’˜µ)∑SUnß;œÄÉVlåÜaü\«\÷\Ï\"X \Îjm_4õ§@∞#$ï\—nb\‚+hﬁÆ\ÓUSM˘\À¿',0,'127.0.0.1','Dubai','United Arab Emirates',25.2048,55.2708,'127.0.0.1','Localhost','Local Development',0,0,NULL,567,477,'2026-03-26',477,'2026-03-26',500,5000),(7,'Brook Bergstrom','brook10@ethereal.email','$2b$12$spUgrpswagCsSiGg9yihS.b6g/LxgzURmFjpb3WIgVled3vpsS4Fq','customer',0,0,'2026-03-23 23:15:00',NULL,'QBORBT2DHLAT7TKJFVQLBAOYKH2DELMP',0,NULL,0,NULL,NULL,NULL,NULL,0,'cjUouiml6V4o1KKbDYj3aImYIaD-LJEpJ9uWa9tNui8','2026-03-24 23:16:44',NULL,NULL,0,'127.0.0.1','New York','United States',40.7128,-74.006,NULL,'New York','United States',40.7128,-74.006,NULL,1000,0,'2026-03-26',0,'2026-03-26',500,5000),(8,' Eve Frami','eve.frami@ethereal.email','$2b$12$DCZ8KItovmzUEHEh1ufbXuskRUOfY4pnE55cURO47.QPYZiAT8diW','customer',0,0,'2026-03-23 23:17:46','2026-03-24 02:44:57','IVG6S3XXQZ62PRUH5EZVXXOJTQMWDVBH',0,NULL,0,NULL,NULL,NULL,NULL,1,'oimMD1oGB6J8O_VY8TH1aBH8FhyblWNHgPeaDe-OZcU','2026-03-24 23:22:27',NULL,NULL,0,'127.0.0.1','Localhost','Local Development',0,0,'127.0.0.1','Localhost','Local Development',0,0,NULL,1450,0,'2026-03-26',0,'2026-03-26',500,5000),(9,'real_location_user','real@example.com','$2b$12$YourHashHere','customer',NULL,NULL,'2026-03-24 02:52:10',NULL,NULL,NULL,NULL,0,NULL,NULL,NULL,NULL,1,NULL,NULL,NULL,NULL,0,NULL,'London','United Kingdom',51.5074,-0.1278,NULL,'London','United Kingdom',51.5074,-0.1278,NULL,1000,0,'2026-03-26',0,'2026-03-26',500,5000),(10,'q','zachery.botsford@ethereal.email','$2b$12$O2JlXZc8RKbpqpwLUT4hUOzXaNUHbfxJZCq5LVbePYaAnRH3UTeE.','customer',1,0,'2026-03-24 03:08:38',NULL,'XVFRP5CLKD5APYH7Y2JLQC3L6DGLLO3K',0,NULL,0,NULL,NULL,NULL,NULL,0,'3PrGf_8n4wdCeTO0m3sckbHStUsfzMDLQvLtm6Eri9w','2026-03-25 03:08:39',NULL,NULL,0,'127.0.0.1','Localhost','Local Development',0,0,NULL,NULL,NULL,NULL,NULL,NULL,1000,0,'2026-03-26',0,'2026-03-26',500,5000),(11,'s','test@test.com','$2b$12$Z7d1Z0Jo.Xrz9B/rACcwY.iIA1RYW7qea/LMgKFicvF/IdNG1EHzK','customer',0,0,'2026-03-24 21:04:46',NULL,'PMRYMMITWUCLMF3NJCEFS7GQXKOO3K4G',0,NULL,0,NULL,NULL,NULL,NULL,1,'7IRtnljz4yQizObqWf9Lmth7hJGLZH-XKgHAMcI8nX8','2026-03-25 21:04:47',NULL,NULL,0,'127.0.0.1','Localhost','Local Development',0,0,NULL,NULL,NULL,NULL,NULL,NULL,1000,0,'2026-03-26',0,'2026-03-26',500,5000),(12,'ali','annamarie.nicolas83@ethereal.email','$2b$12$TDaFFqbbfny73MoRDN9wDOsuu/LSACwGcQhplHFBxI.6M8lIwuMq2','customer',0,0,'2026-03-25 21:01:24','2026-03-25 21:09:18','SNRRVLOINUFJALSHIE6ZIQZTKLFEFNLJ',0,NULL,0,NULL,NULL,NULL,NULL,1,'epHC3NEIe6kXWgfYXm3eu1K5FBwgB16q7IGq4juLypU','2026-03-26 21:01:24',NULL,NULL,0,'127.0.0.1','Localhost','Local Development',0,0,'127.0.0.1','Localhost','Local Development',0,0,NULL,1000,0,'2026-03-26',0,'2026-03-26',500,5000),(13,'ayan','ffid4554@gmail.com','$2b$12$FeSEFDHN.61ZlO9HO0DFQet9Rmim54Qomh4/i5INO4i4ECbiHipzO','customer',0,1,'2026-03-26 17:07:05',NULL,'46FWIBBNHYDLURYV5LXCKXVWTM2VI7WV',0,NULL,0,NULL,NULL,NULL,NULL,0,'eUuZK2KxPeyJlH14wKJrEVCESZi_uFVe0GzyXN_A_eg','2026-03-27 17:07:07',NULL,NULL,0,'127.0.0.1','Localhost','Local Development',0,0,NULL,NULL,NULL,NULL,NULL,NULL,1000,0,'2026-03-26',0,'2026-03-26',500,5000),(14,'chayan','foodpanda00881122@gmail.com','$2b$12$yOk8zvqzrB5Fzqxr6w61GeSSOLBM0y2hoWc65GFetXoa2EzW1aeQa','customer',0,1,'2026-03-26 17:12:08','2026-03-26 17:14:36','GDRZ4447QHWL7NYA7TPQXWZ3ILPL2IWB',0,NULL,0,NULL,NULL,NULL,NULL,1,NULL,NULL,NULL,NULL,0,'127.0.0.1','Localhost','Local Development',0,0,'127.0.0.1','Localhost','Local Development',0,0,NULL,1003,0,'2026-03-26',0,'2026-03-26',500,5000),(15,'Legendarybrotherqk@gmail.com','Legendarybrotherqk@gmail.com','$2b$12$kNpWdCJ9KgILFonfwcx.ee2Ql1euxHBSDA58miCtPJRwTbuz9mXsW','customer',0,1,'2026-03-26 17:24:25','2026-03-26 17:24:50','RJAWQCKRLU67GGMN37W77QWHJX3HZ5WE',0,'255288555',0,NULL,NULL,NULL,NULL,1,NULL,NULL,NULL,NULL,0,'127.0.0.1','Localhost','Local Development',0,0,'127.0.0.1','Localhost','Local Development',0,0,NULL,1200,0,'2026-03-26',0,'2026-03-26',500,5000),(16,'testuser','test@example.com','$2b$12$8PvK5q8ZqU5jqX8qZqU5jq','customer',NULL,NULL,NULL,NULL,NULL,NULL,'447301319668',1,NULL,NULL,NULL,NULL,1,NULL,NULL,NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,1000,0,NULL,0,NULL,500,5000),(18,'mynewuser','mynewuser@example.com','$2b$12$8PvK5q8ZqU5jqX8qZqU5jq','admin',NULL,NULL,'2026-03-29 09:25:08',NULL,NULL,NULL,'447301319668',1,NULL,NULL,NULL,NULL,1,NULL,NULL,NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,1000,0,NULL,0,NULL,500,5000),(20,'AR','abdulrahiim87@gmail.com','$2b$12$Xicp2LLcCTGKH2rtitUFT.9bjepdebZEDNzxI5f9itAUnnEu.AwCG','customer',0,0,'2026-04-13 23:19:42','2026-04-14 21:07:18','UOM33VSYZHPZ46DGPZ47Z452L4NCALRU',1,'+447301319668',1,NULL,NULL,NULL,NULL,1,NULL,NULL,_binary 'cQø3+§`~\√Ä€•',_binary '•& !X õïv©Rq\ﬂ{m6´\ÈπVP\—»Ö	êV\ÓÇÅë7(\“¿\"X Fc]ºy(\ÁàY\05\€/ΩT÷±\Î+;òl\ÓE\Óò#|∑è',0,'127.0.0.1','Localhost','Local Development',0,0,'127.0.0.1','Localhost','Local Development',0,0,NULL,966,34,'2026-04-14',34,'2026-04-14',500,5000);
/*!40000 ALTER TABLE `user` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping routines for database 'zero_trust_db'
--
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-04-17  2:56:07
