--
-- PostgreSQL database dump
--

\restrict 4KJYxRD9Fh4Z0pO6GuQz9gM4XL4YwlPbVaSAFrC3hDvvVj27SPyszObQZnGkBYR

-- Dumped from database version 17.5
-- Dumped by pg_dump version 17.6

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: public; Type: SCHEMA; Schema: -; Owner: postgres
--

-- *not* creating schema, since initdb creates it


ALTER SCHEMA public OWNER TO postgres;

--
-- Name: SCHEMA public; Type: COMMENT; Schema: -; Owner: postgres
--

COMMENT ON SCHEMA public IS '';


--
-- Name: DeductionType; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public."DeductionType" AS ENUM (
    'PERSONAL',
    'SPOUSE',
    'CHILD',
    'PARENT',
    'LIFE_INSURANCE',
    'HEALTH_INSURANCE',
    'PROVIDENT_FUND',
    'RMF',
    'SSF',
    'DONATION',
    'HOME_LOAN',
    'OTHER'
);


ALTER TYPE public."DeductionType" OWNER TO postgres;

--
-- Name: IncomeType; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public."IncomeType" AS ENUM (
    'SALARY',
    'FREELANCE',
    'BUSINESS',
    'INVESTMENT',
    'RENTAL',
    'OTHER'
);


ALTER TYPE public."IncomeType" OWNER TO postgres;

--
-- Name: Language; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public."Language" AS ENUM (
    'TH',
    'EN'
);


ALTER TYPE public."Language" OWNER TO postgres;

--
-- Name: NotificationChannel; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public."NotificationChannel" AS ENUM (
    'EMAIL',
    'SMS',
    'NONE'
);


ALTER TYPE public."NotificationChannel" OWNER TO postgres;

--
-- Name: TaxFilingStatus; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public."TaxFilingStatus" AS ENUM (
    'DRAFT',
    'SUBMITTED'
);


ALTER TYPE public."TaxFilingStatus" OWNER TO postgres;

--
-- Name: TaxFormType; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public."TaxFormType" AS ENUM (
    'PND90',
    'PND91',
    'PND94'
);


ALTER TYPE public."TaxFormType" OWNER TO postgres;

--
-- Name: TaxType; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public."TaxType" AS ENUM (
    'INDIVIDUAL'
);


ALTER TYPE public."TaxType" OWNER TO postgres;

--
-- Name: UserTokenType; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public."UserTokenType" AS ENUM (
    'PASSWORD_RESET',
    'PASSWORD_CHANGE',
    'NEW_DEVICE_CONFIRM',
    'EMAIL_VERIFY'
);


ALTER TYPE public."UserTokenType" OWNER TO postgres;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: _prisma_migrations; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public._prisma_migrations (
    id character varying(36) NOT NULL,
    checksum character varying(64) NOT NULL,
    finished_at timestamp with time zone,
    migration_name character varying(255) NOT NULL,
    logs text,
    rolled_back_at timestamp with time zone,
    started_at timestamp with time zone DEFAULT now() NOT NULL,
    applied_steps_count integer DEFAULT 0 NOT NULL
);


ALTER TABLE public._prisma_migrations OWNER TO postgres;

--
-- Name: accounts; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.accounts (
    id text NOT NULL,
    "userId" text NOT NULL,
    type text NOT NULL,
    provider text NOT NULL,
    "providerAccountId" text NOT NULL,
    refresh_token text,
    access_token text,
    expires_at integer,
    token_type text,
    scope text,
    id_token text,
    session_state text
);


ALTER TABLE public.accounts OWNER TO postgres;

--
-- Name: deduction_records; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.deduction_records (
    id text NOT NULL,
    "userId" text NOT NULL,
    type public."DeductionType" NOT NULL,
    amount numeric(12,2) NOT NULL,
    description text,
    date timestamp(3) without time zone NOT NULL,
    "taxYear" integer NOT NULL,
    "documentId" text,
    "createdAt" timestamp(3) without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "updatedAt" timestamp(3) without time zone NOT NULL
);


ALTER TABLE public.deduction_records OWNER TO postgres;

--
-- Name: document_files; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.document_files (
    id text NOT NULL,
    name character varying(200) NOT NULL,
    content text,
    "fileUrl" text,
    "fileName" character varying(255),
    "fileSize" integer,
    "mimeType" character varying(100),
    "isUploaded" boolean DEFAULT false NOT NULL,
    type text,
    tags text[] DEFAULT ARRAY[]::text[],
    "isDeleted" boolean DEFAULT false NOT NULL,
    "deletedAt" timestamp(3) without time zone,
    "folderId" text,
    "userId" text NOT NULL,
    "createdAt" timestamp(3) without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "updatedAt" timestamp(3) without time zone NOT NULL
);


ALTER TABLE public.document_files OWNER TO postgres;

--
-- Name: document_folders; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.document_folders (
    id text NOT NULL,
    name character varying(200) NOT NULL,
    color text DEFAULT '#3B82F6'::text NOT NULL,
    "userId" text NOT NULL,
    "parentId" text,
    "isDeleted" boolean DEFAULT false NOT NULL,
    "deletedAt" timestamp(3) without time zone,
    "createdAt" timestamp(3) without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "updatedAt" timestamp(3) without time zone NOT NULL
);


ALTER TABLE public.document_folders OWNER TO postgres;

--
-- Name: income_records; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.income_records (
    id text NOT NULL,
    "userId" text NOT NULL,
    type public."IncomeType" NOT NULL,
    amount numeric(12,2) NOT NULL,
    description text,
    date timestamp(3) without time zone NOT NULL,
    "taxYear" integer NOT NULL,
    "documentId" text,
    "createdAt" timestamp(3) without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "updatedAt" timestamp(3) without time zone NOT NULL
);


ALTER TABLE public.income_records OWNER TO postgres;

--
-- Name: sessions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.sessions (
    id text NOT NULL,
    "sessionToken" text NOT NULL,
    "userId" text NOT NULL,
    expires timestamp(3) without time zone NOT NULL
);


ALTER TABLE public.sessions OWNER TO postgres;

--
-- Name: tax_filings; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.tax_filings (
    id text NOT NULL,
    "userId" text NOT NULL,
    "taxYear" integer NOT NULL,
    "formType" public."TaxFormType" NOT NULL,
    status public."TaxFilingStatus" DEFAULT 'DRAFT'::public."TaxFilingStatus" NOT NULL,
    "totalIncome" numeric(12,2),
    "totalDeduction" numeric(12,2),
    "taxAmount" numeric(12,2),
    "submittedAt" timestamp(3) without time zone,
    notes text,
    "createdAt" timestamp(3) without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "updatedAt" timestamp(3) without time zone NOT NULL
);


ALTER TABLE public.tax_filings OWNER TO postgres;

--
-- Name: user_tokens; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.user_tokens (
    id text NOT NULL,
    "userId" text NOT NULL,
    type public."UserTokenType" NOT NULL,
    "tokenHash" text NOT NULL,
    expires timestamp(3) without time zone NOT NULL,
    "usedAt" timestamp(3) without time zone,
    "createdAt" timestamp(3) without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE public.user_tokens OWNER TO postgres;

--
-- Name: users; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.users (
    id text NOT NULL,
    name text,
    "firstName" character varying(120),
    "lastName" character varying(160),
    email text NOT NULL,
    password text NOT NULL,
    phone character varying(20),
    "dateOfBirth" timestamp(3) without time zone,
    address text,
    district character varying(100),
    province character varying(100),
    "postalCode" character varying(10),
    occupation character varying(120),
    "annualIncome" numeric(12,2),
    language public."Language" DEFAULT 'TH'::public."Language" NOT NULL,
    "taxType" public."TaxType" DEFAULT 'INDIVIDUAL'::public."TaxType" NOT NULL,
    "emailVerified" timestamp(3) without time zone,
    image text,
    "notifyOnPasswordChange" public."NotificationChannel" DEFAULT 'EMAIL'::public."NotificationChannel" NOT NULL,
    "notifyEmail" boolean DEFAULT true NOT NULL,
    "notifySms" boolean DEFAULT false NOT NULL,
    "notifyTaxDeadlines" boolean DEFAULT true NOT NULL,
    "notifyReports" boolean DEFAULT true NOT NULL,
    "createdAt" timestamp(3) without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "updatedAt" timestamp(3) without time zone NOT NULL
);


ALTER TABLE public.users OWNER TO postgres;

--
-- Data for Name: _prisma_migrations; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public._prisma_migrations (id, checksum, finished_at, migration_name, logs, rolled_back_at, started_at, applied_steps_count) FROM stdin;
d389f46c-ad23-40ba-8411-7a9ba0fbedfa	18f3241654608fb567ed8193fa3162b9a421b600750deacbfa20dbe406d34f4e	2025-10-19 18:24:43.262522+07	20250818195016_add_phone_and_notify_channel		\N	2025-10-19 18:24:43.262522+07	0
786a4362-81e0-43c8-b57e-5326f7d43862	1b872b10ffe418eb67b6721acff61106ea10e9984917d2490ce13d9e28f1c5b4	2025-10-19 18:24:44.104574+07	20250819133003_revamp_verification_token		\N	2025-10-19 18:24:44.104574+07	0
4736deb4-8012-476c-87b2-e1373a77db90	a2eefb80f0c4593d2916a201bfe3beb746e14331a033edaea3353006a63c7a14	2025-10-19 18:24:44.791003+07	20250918095443_add_first_last_name		\N	2025-10-19 18:24:44.791003+07	0
e75e2c9a-904b-4623-befc-55aff1224b3b	282c69d1e09cac244e3fe7415848eabac2f0f8abe74d18bc4f8b0c52c7724bab	2025-10-19 18:24:45.482742+07	20250919074804_sync_profile_fields		\N	2025-10-19 18:24:45.482742+07	0
5405d1e2-b7c6-4ad3-b5fb-13845523545b	e318cb3d876a3bdf740383b9b319302803c5c5ab9961953bc22e391abfe1490c	2025-10-19 18:24:46.187764+07	20250919080142_add_profile_fields		\N	2025-10-19 18:24:46.187764+07	0
958eb399-1a16-457a-8c00-08787244ad18	bd22a82990b2003507b215c6c2d5e3ae53d99c7e3dc61b7d2d1a6bf1e4017485	2025-10-19 18:24:46.852923+07	20250919093555_add_document_model		\N	2025-10-19 18:24:46.852923+07	0
63b76b5a-3f2b-4984-9966-61b593775e46	e423038c460e91d17423df65ee8d9ebce90c38ae3f44569d069d9c8a710fd598	2025-10-19 18:24:47.513282+07	20250919095151_fix_user_documentfolder_relations		\N	2025-10-19 18:24:47.513282+07	0
34d074c2-7e10-42f1-aaff-5afab6466cd6	32ec502266b8cbf72d00126273f04483e88f0b746645249975708cdc952fc7ac	2025-10-19 18:24:48.207817+07	20250922115055_add_file_upload_fields		\N	2025-10-19 18:24:48.207817+07	0
8603996a-b79c-4093-9644-9b2d67abde5f	8fc83b3da70fc2b486d39356fb1ede54704c20359d3f888c1713a9fea33401e5	2025-10-19 18:24:48.880957+07	20251016095323_add_notification_model		\N	2025-10-19 18:24:48.880957+07	0
2ccf9b16-7d1f-4f95-9d1d-d93356d03d29	e9c011bb238d629fc12d0ff4ea768b6c1e8325872075a49eca94c11b74e033ea	2025-10-19 18:24:49.543086+07	20251016100445_add_soft_delete_to_documents		\N	2025-10-19 18:24:49.543086+07	0
\.


--
-- Data for Name: accounts; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.accounts (id, "userId", type, provider, "providerAccountId", refresh_token, access_token, expires_at, token_type, scope, id_token, session_state) FROM stdin;
\.


--
-- Data for Name: deduction_records; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.deduction_records (id, "userId", type, amount, description, date, "taxYear", "documentId", "createdAt", "updatedAt") FROM stdin;
\.


--
-- Data for Name: document_files; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.document_files (id, name, content, "fileUrl", "fileName", "fileSize", "mimeType", "isUploaded", type, tags, "isDeleted", "deletedAt", "folderId", "userId", "createdAt", "updatedAt") FROM stdin;
cmh3vtar5000b92djkgwym4sw	เงินเดือน.png	\N	https://smart-tax-assistant-uploads.s3.ap-southeast-1.amazonaws.com/documents/cmgxmh7oq000092dj3cr9huni/1761251742888_Screenshot_2568-10-24_at_02.29.43.png	Screenshot 2568-10-24 at 02.29.43.png	617228	image/png	t	TAX_FORM	{}	f	\N	cmh3um0m8000692dj5lz2q4ae	cmgxmh7oq000092dj3cr9huni	2025-10-23 20:35:43.408	2025-10-23 20:36:00.392
cmh4snzc2000192tcd6w1jpcr	tax121260.pdf	\N	https://smart-tax-assistant-uploads.s3.ap-southeast-1.amazonaws.com/documents/cmgxmh7oq000092dj3cr9huni/1761306922263_tax121260.pdf	tax121260.pdf	142556	application/pdf	t	TAX_FORM	{}	f	\N	cmh3um0m8000692dj5lz2q4ae	cmgxmh7oq000092dj3cr9huni	2025-10-24 11:55:22.658	2025-10-24 11:55:22.658
\.


--
-- Data for Name: document_folders; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.document_folders (id, name, color, "userId", "parentId", "isDeleted", "deletedAt", "createdAt", "updatedAt") FROM stdin;
cmh3um0m8000692dj5lz2q4ae	รายรับเดือนมีนา	#3B82F6	cmgxmh7oq000092dj3cr9huni	\N	f	\N	2025-10-23 20:02:04.049	2025-10-23 20:02:04.049
\.


--
-- Data for Name: income_records; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.income_records (id, "userId", type, amount, description, date, "taxYear", "documentId", "createdAt", "updatedAt") FROM stdin;
\.


--
-- Data for Name: sessions; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.sessions (id, "sessionToken", "userId", expires) FROM stdin;
\.


--
-- Data for Name: tax_filings; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.tax_filings (id, "userId", "taxYear", "formType", status, "totalIncome", "totalDeduction", "taxAmount", "submittedAt", notes, "createdAt", "updatedAt") FROM stdin;
\.


--
-- Data for Name: user_tokens; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.user_tokens (id, "userId", type, "tokenHash", expires, "usedAt", "createdAt") FROM stdin;
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.users (id, name, "firstName", "lastName", email, password, phone, "dateOfBirth", address, district, province, "postalCode", occupation, "annualIncome", language, "taxType", "emailVerified", image, "notifyOnPasswordChange", "notifyEmail", "notifySms", "notifyTaxDeadlines", "notifyReports", "createdAt", "updatedAt") FROM stdin;
cmgxmh7oq000092dj3cr9huni	Atikun Pidsayo	Atikun	Pidsayo	atikun145@gmail.com	$2b$12$lDfKhu4LtC9Z9iP41BvdBue7SS9qH2Dzriltq.GdvIRLTXD9thPeK	0931012808	2002-12-18 00:00:00	\N	\N	\N	\N	\N	\N	TH	INDIVIDUAL	\N	\N	EMAIL	t	f	t	t	2025-10-19 11:27:45.961	2025-10-19 11:29:37.038
cmhaklbua000092mu5wcl1xk3	รวิพล สอาดโพธิ์ทอง	รวิพล	สอาดโพธิ์ทอง	mean112546@gmail.com	$2b$12$mFNfRwioSaO0ebA0su46S.yUk2pZvSRbKYHPHRElcCly4iqqJmlqK	\N	\N	\N	\N	\N	\N	\N	\N	TH	INDIVIDUAL	\N	\N	EMAIL	t	f	t	t	2025-10-28 12:55:59.026	2025-10-28 12:55:59.026
\.


--
-- Name: _prisma_migrations _prisma_migrations_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public._prisma_migrations
    ADD CONSTRAINT _prisma_migrations_pkey PRIMARY KEY (id);


--
-- Name: accounts accounts_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.accounts
    ADD CONSTRAINT accounts_pkey PRIMARY KEY (id);


--
-- Name: deduction_records deduction_records_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.deduction_records
    ADD CONSTRAINT deduction_records_pkey PRIMARY KEY (id);


--
-- Name: document_files document_files_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.document_files
    ADD CONSTRAINT document_files_pkey PRIMARY KEY (id);


--
-- Name: document_folders document_folders_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.document_folders
    ADD CONSTRAINT document_folders_pkey PRIMARY KEY (id);


--
-- Name: income_records income_records_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.income_records
    ADD CONSTRAINT income_records_pkey PRIMARY KEY (id);


--
-- Name: sessions sessions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.sessions
    ADD CONSTRAINT sessions_pkey PRIMARY KEY (id);


--
-- Name: tax_filings tax_filings_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tax_filings
    ADD CONSTRAINT tax_filings_pkey PRIMARY KEY (id);


--
-- Name: user_tokens user_tokens_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_tokens
    ADD CONSTRAINT user_tokens_pkey PRIMARY KEY (id);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: accounts_provider_providerAccountId_key; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX "accounts_provider_providerAccountId_key" ON public.accounts USING btree (provider, "providerAccountId");


--
-- Name: deduction_records_userId_taxYear_idx; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX "deduction_records_userId_taxYear_idx" ON public.deduction_records USING btree ("userId", "taxYear");


--
-- Name: document_files_folderId_idx; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX "document_files_folderId_idx" ON public.document_files USING btree ("folderId");


--
-- Name: document_files_userId_idx; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX "document_files_userId_idx" ON public.document_files USING btree ("userId");


--
-- Name: document_files_userId_isDeleted_idx; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX "document_files_userId_isDeleted_idx" ON public.document_files USING btree ("userId", "isDeleted");


--
-- Name: document_folders_parentId_idx; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX "document_folders_parentId_idx" ON public.document_folders USING btree ("parentId");


--
-- Name: document_folders_userId_idx; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX "document_folders_userId_idx" ON public.document_folders USING btree ("userId");


--
-- Name: document_folders_userId_isDeleted_idx; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX "document_folders_userId_isDeleted_idx" ON public.document_folders USING btree ("userId", "isDeleted");


--
-- Name: income_records_userId_taxYear_idx; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX "income_records_userId_taxYear_idx" ON public.income_records USING btree ("userId", "taxYear");


--
-- Name: sessions_sessionToken_key; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX "sessions_sessionToken_key" ON public.sessions USING btree ("sessionToken");


--
-- Name: tax_filings_userId_taxYear_idx; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX "tax_filings_userId_taxYear_idx" ON public.tax_filings USING btree ("userId", "taxYear");


--
-- Name: user_tokens_expires_idx; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX user_tokens_expires_idx ON public.user_tokens USING btree (expires);


--
-- Name: user_tokens_tokenHash_key; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX "user_tokens_tokenHash_key" ON public.user_tokens USING btree ("tokenHash");


--
-- Name: user_tokens_userId_type_idx; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX "user_tokens_userId_type_idx" ON public.user_tokens USING btree ("userId", type);


--
-- Name: users_email_key; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX users_email_key ON public.users USING btree (email);


--
-- Name: users_phone_key; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX users_phone_key ON public.users USING btree (phone);


--
-- Name: accounts accounts_userId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.accounts
    ADD CONSTRAINT "accounts_userId_fkey" FOREIGN KEY ("userId") REFERENCES public.users(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: deduction_records deduction_records_documentId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.deduction_records
    ADD CONSTRAINT "deduction_records_documentId_fkey" FOREIGN KEY ("documentId") REFERENCES public.document_files(id) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: deduction_records deduction_records_userId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.deduction_records
    ADD CONSTRAINT "deduction_records_userId_fkey" FOREIGN KEY ("userId") REFERENCES public.users(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: document_files document_files_folderId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.document_files
    ADD CONSTRAINT "document_files_folderId_fkey" FOREIGN KEY ("folderId") REFERENCES public.document_folders(id) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: document_files document_files_userId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.document_files
    ADD CONSTRAINT "document_files_userId_fkey" FOREIGN KEY ("userId") REFERENCES public.users(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: document_folders document_folders_parentId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.document_folders
    ADD CONSTRAINT "document_folders_parentId_fkey" FOREIGN KEY ("parentId") REFERENCES public.document_folders(id) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: document_folders document_folders_userId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.document_folders
    ADD CONSTRAINT "document_folders_userId_fkey" FOREIGN KEY ("userId") REFERENCES public.users(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: income_records income_records_documentId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.income_records
    ADD CONSTRAINT "income_records_documentId_fkey" FOREIGN KEY ("documentId") REFERENCES public.document_files(id) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: income_records income_records_userId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.income_records
    ADD CONSTRAINT "income_records_userId_fkey" FOREIGN KEY ("userId") REFERENCES public.users(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: sessions sessions_userId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.sessions
    ADD CONSTRAINT "sessions_userId_fkey" FOREIGN KEY ("userId") REFERENCES public.users(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: tax_filings tax_filings_userId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tax_filings
    ADD CONSTRAINT "tax_filings_userId_fkey" FOREIGN KEY ("userId") REFERENCES public.users(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: user_tokens user_tokens_userId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_tokens
    ADD CONSTRAINT "user_tokens_userId_fkey" FOREIGN KEY ("userId") REFERENCES public.users(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: SCHEMA public; Type: ACL; Schema: -; Owner: postgres
--

REVOKE USAGE ON SCHEMA public FROM PUBLIC;


--
-- PostgreSQL database dump complete
--

\unrestrict 4KJYxRD9Fh4Z0pO6GuQz9gM4XL4YwlPbVaSAFrC3hDvvVj27SPyszObQZnGkBYR

