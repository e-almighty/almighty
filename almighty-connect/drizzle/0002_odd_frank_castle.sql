CREATE TABLE `push_keys` (
	`id` text PRIMARY KEY NOT NULL,
	`public_jwk` text NOT NULL,
	`private_jwk` text NOT NULL,
	`created` integer NOT NULL
);
--> statement-breakpoint
CREATE TABLE `push_subscriptions` (
	`endpoint` text PRIMARY KEY NOT NULL,
	`tenant` text NOT NULL,
	`slot` text NOT NULL,
	`p256dh` text NOT NULL,
	`auth` text NOT NULL,
	`client` text,
	`created` integer NOT NULL
);
