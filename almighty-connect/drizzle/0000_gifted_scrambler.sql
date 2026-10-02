CREATE TABLE `consultations` (
	`id` text PRIMARY KEY NOT NULL,
	`tenant` text NOT NULL,
	`store` text NOT NULL,
	`staff` text,
	`status` text NOT NULL,
	`created` integer NOT NULL,
	`expires` integer NOT NULL,
	`version` integer DEFAULT 0 NOT NULL,
	`payload` text NOT NULL
);
--> statement-breakpoint
CREATE UNIQUE INDEX `one_open_store` ON `consultations` (`tenant`,`store`) WHERE "consultations"."status" != 'ended';--> statement-breakpoint
CREATE UNIQUE INDEX `one_active_staff` ON `consultations` (`tenant`,`staff`) WHERE "consultations"."status" = 'active';--> statement-breakpoint
CREATE TABLE `presence` (
	`tenant` text NOT NULL,
	`slot` text NOT NULL,
	`ready` integer NOT NULL,
	`seen` integer NOT NULL,
	PRIMARY KEY(`tenant`, `slot`)
);
