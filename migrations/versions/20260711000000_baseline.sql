-- Baseline schema: users table.
CREATE TABLE "users" (
    "id"         uuid          NOT NULL,
    "email"      varchar(320)  NOT NULL,
    "full_name"  varchar(200)  NOT NULL,
    "role"       varchar(32)   NOT NULL DEFAULT 'member',
    "is_active"  boolean       NOT NULL DEFAULT true,
    "created_at" timestamptz   NOT NULL DEFAULT now(),
    "updated_at" timestamptz   NOT NULL DEFAULT now(),
    PRIMARY KEY ("id"),
    CONSTRAINT "uq_users_email" UNIQUE ("email")
);
CREATE INDEX "ix_users_email" ON "users" ("email");
