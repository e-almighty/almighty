CREATE TABLE `receiver_connections` (
	`tenant` text NOT NULL,
	`slot` text NOT NULL,
	`client` text NOT NULL,
	`ready` integer NOT NULL,
	`seen` integer NOT NULL,
	PRIMARY KEY(`tenant`, `slot`, `client`)
);
