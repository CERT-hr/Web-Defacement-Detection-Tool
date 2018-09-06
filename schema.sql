--
-- PostgreSQL database dump
--

-- Dumped from database version 9.5.10
-- Dumped by pg_dump version 9.5.10

SET statement_timeout = 0;
SET lock_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: plpgsql; Type: EXTENSION; Schema: -; Owner: 
--

CREATE EXTENSION IF NOT EXISTS plpgsql WITH SCHEMA pg_catalog;


--
-- Name: EXTENSION plpgsql; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION plpgsql IS 'PL/pgSQL procedural language';


SET search_path = public, pg_catalog;

--
-- Name: deface_signature_id_seq; Type: SEQUENCE; Schema: public; Owner: webdfc
--

CREATE SEQUENCE deface_signature_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE deface_signature_id_seq OWNER TO webdfc;

SET default_tablespace = '';

SET default_with_oids = false;

--
-- Name: deface_signature; Type: TABLE; Schema: public; Owner: webdfc
--

CREATE TABLE deface_signature (
    id integer DEFAULT nextval('deface_signature_id_seq'::regclass) NOT NULL,
    notifier_id integer NOT NULL,
    detection integer NOT NULL,
    "timestamp" timestamp with time zone NOT NULL
);


ALTER TABLE deface_signature OWNER TO webdfc;

--
-- Name: COLUMN deface_signature.detection; Type: COMMENT; Schema: public; Owner: webdfc
--

COMMENT ON COLUMN deface_signature.detection IS '0 - complete
1 - not complete';


--
-- Name: defaces_id_seq; Type: SEQUENCE; Schema: public; Owner: webdfc
--

CREATE SEQUENCE defaces_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE defaces_id_seq OWNER TO webdfc;

--
-- Name: defaces; Type: TABLE; Schema: public; Owner: webdfc
--

CREATE TABLE defaces (
    id integer DEFAULT nextval('defaces_id_seq'::regclass) NOT NULL,
    "time" timestamp with time zone NOT NULL,
    notifier_id integer NOT NULL,
    url character varying NOT NULL,
    mirrorsrc character varying DEFAULT 'http://zone-h.org/'::character varying NOT NULL
);


ALTER TABLE defaces OWNER TO webdfc;

--
-- Name: defaces_elements_defaces_id_seq; Type: SEQUENCE; Schema: public; Owner: webdfc
--

CREATE SEQUENCE defaces_elements_defaces_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE defaces_elements_defaces_id_seq OWNER TO webdfc;

--
-- Name: defaces_elements_defaces; Type: TABLE; Schema: public; Owner: webdfc
--

CREATE TABLE defaces_elements_defaces (
    id integer DEFAULT nextval('defaces_elements_defaces_id_seq'::regclass) NOT NULL,
    defaces_id integer NOT NULL,
    elements_defaces_id integer NOT NULL
);


ALTER TABLE defaces_elements_defaces OWNER TO webdfc;

--
-- Name: defaces_signature_elements_dfcsign_id_seq; Type: SEQUENCE; Schema: public; Owner: webdfc
--

CREATE SEQUENCE defaces_signature_elements_dfcsign_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE defaces_signature_elements_dfcsign_id_seq OWNER TO webdfc;

--
-- Name: defaces_signature_elements_dfcsign; Type: TABLE; Schema: public; Owner: webdfc
--

CREATE TABLE defaces_signature_elements_dfcsign (
    id integer DEFAULT nextval('defaces_signature_elements_dfcsign_id_seq'::regclass) NOT NULL,
    deface_signature_id integer NOT NULL,
    elements_dfcsign_id integer NOT NULL
);


ALTER TABLE defaces_signature_elements_dfcsign OWNER TO webdfc;

--
-- Name: elements_defaces_id_seq; Type: SEQUENCE; Schema: public; Owner: webdfc
--

CREATE SEQUENCE elements_defaces_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE elements_defaces_id_seq OWNER TO webdfc;

--
-- Name: elements_defaces; Type: TABLE; Schema: public; Owner: webdfc
--

CREATE TABLE elements_defaces (
    id integer DEFAULT nextval('elements_defaces_id_seq'::regclass) NOT NULL,
    type character varying NOT NULL,
    element bytea,
    hash character varying,
    resource character varying
);


ALTER TABLE elements_defaces OWNER TO webdfc;

--
-- Name: elements_dfcsign_id_seq; Type: SEQUENCE; Schema: public; Owner: webdfc
--

CREATE SEQUENCE elements_dfcsign_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE elements_dfcsign_id_seq OWNER TO webdfc;

--
-- Name: elements_dfcsign; Type: TABLE; Schema: public; Owner: webdfc
--

CREATE TABLE elements_dfcsign (
    id integer DEFAULT nextval('elements_dfcsign_id_seq'::regclass) NOT NULL,
    type character varying NOT NULL,
    element bytea,
    hash character varying,
    resource character varying
);


ALTER TABLE elements_dfcsign OWNER TO webdfc;

--
-- Name: notifier_id_seq; Type: SEQUENCE; Schema: public; Owner: webdfc
--

CREATE SEQUENCE notifier_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE notifier_id_seq OWNER TO webdfc;

--
-- Name: notifier; Type: TABLE; Schema: public; Owner: webdfc
--

CREATE TABLE notifier (
    id integer DEFAULT nextval('notifier_id_seq'::regclass) NOT NULL,
    name character varying NOT NULL,
    sample_start_date time with time zone,
    current_sample_size integer
);


ALTER TABLE notifier OWNER TO webdfc;

--
-- Name: deface_signature_pkey; Type: CONSTRAINT; Schema: public; Owner: webdfc
--

ALTER TABLE ONLY deface_signature
    ADD CONSTRAINT deface_signature_pkey PRIMARY KEY (id);


--
-- Name: defaces_elements_defaces_pkey; Type: CONSTRAINT; Schema: public; Owner: webdfc
--

ALTER TABLE ONLY defaces_elements_defaces
    ADD CONSTRAINT defaces_elements_defaces_pkey PRIMARY KEY (id);


--
-- Name: defaces_pkey; Type: CONSTRAINT; Schema: public; Owner: webdfc
--

ALTER TABLE ONLY defaces
    ADD CONSTRAINT defaces_pkey PRIMARY KEY (id);


--
-- Name: defaces_signature_elements_dfcsign_pkey; Type: CONSTRAINT; Schema: public; Owner: webdfc
--

ALTER TABLE ONLY defaces_signature_elements_dfcsign
    ADD CONSTRAINT defaces_signature_elements_dfcsign_pkey PRIMARY KEY (id);


--
-- Name: elements_defaces_pkey; Type: CONSTRAINT; Schema: public; Owner: webdfc
--

ALTER TABLE ONLY elements_defaces
    ADD CONSTRAINT elements_defaces_pkey PRIMARY KEY (id);


--
-- Name: elements_signature_pkey; Type: CONSTRAINT; Schema: public; Owner: webdfc
--

ALTER TABLE ONLY elements_dfcsign
    ADD CONSTRAINT elements_signature_pkey PRIMARY KEY (id);


--
-- Name: notifier_pkey; Type: CONSTRAINT; Schema: public; Owner: webdfc
--

ALTER TABLE ONLY notifier
    ADD CONSTRAINT notifier_pkey PRIMARY KEY (id);


--
-- Name: fki_deface_signature_notifier_id_fkey; Type: INDEX; Schema: public; Owner: webdfc
--

CREATE INDEX fki_deface_signature_notifier_id_fkey ON deface_signature USING btree (notifier_id);


--
-- Name: fki_defaces_elements_defaces_defaces_id_fkey; Type: INDEX; Schema: public; Owner: webdfc
--

CREATE INDEX fki_defaces_elements_defaces_defaces_id_fkey ON defaces_elements_defaces USING btree (defaces_id);


--
-- Name: fki_defaces_elements_defaces_elements_defaces_id; Type: INDEX; Schema: public; Owner: webdfc
--

CREATE INDEX fki_defaces_elements_defaces_elements_defaces_id ON defaces_elements_defaces USING btree (elements_defaces_id);


--
-- Name: fki_defaces_notifier_id_fkey; Type: INDEX; Schema: public; Owner: webdfc
--

CREATE INDEX fki_defaces_notifier_id_fkey ON defaces USING btree (notifier_id);


--
-- Name: fki_defaces_signature_elements_dfcsign_defaces_signature_id_fke; Type: INDEX; Schema: public; Owner: webdfc
--

CREATE INDEX fki_defaces_signature_elements_dfcsign_defaces_signature_id_fke ON defaces_signature_elements_dfcsign USING btree (deface_signature_id);


--
-- Name: fki_defaces_signature_elements_dfcsign_elements_dfcsign_id_fkey; Type: INDEX; Schema: public; Owner: webdfc
--

CREATE INDEX fki_defaces_signature_elements_dfcsign_elements_dfcsign_id_fkey ON defaces_signature_elements_dfcsign USING btree (elements_dfcsign_id);


--
-- Name: deface_signature_notifier_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: webdfc
--

ALTER TABLE ONLY deface_signature
    ADD CONSTRAINT deface_signature_notifier_id_fkey FOREIGN KEY (notifier_id) REFERENCES notifier(id);


--
-- Name: defaces_elements_defaces_defaces_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: webdfc
--

ALTER TABLE ONLY defaces_elements_defaces
    ADD CONSTRAINT defaces_elements_defaces_defaces_id_fkey FOREIGN KEY (defaces_id) REFERENCES defaces(id);


--
-- Name: defaces_elements_defaces_elements_defaces_id; Type: FK CONSTRAINT; Schema: public; Owner: webdfc
--

ALTER TABLE ONLY defaces_elements_defaces
    ADD CONSTRAINT defaces_elements_defaces_elements_defaces_id FOREIGN KEY (elements_defaces_id) REFERENCES elements_defaces(id);


--
-- Name: defaces_notifier_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: webdfc
--

ALTER TABLE ONLY defaces
    ADD CONSTRAINT defaces_notifier_id_fkey FOREIGN KEY (notifier_id) REFERENCES notifier(id);


--
-- Name: defaces_signature_elements_dfcsign_defaces_signature_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: webdfc
--

ALTER TABLE ONLY defaces_signature_elements_dfcsign
    ADD CONSTRAINT defaces_signature_elements_dfcsign_defaces_signature_id_fkey FOREIGN KEY (deface_signature_id) REFERENCES deface_signature(id);


--
-- Name: defaces_signature_elements_dfcsign_elements_dfcsign_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: webdfc
--

ALTER TABLE ONLY defaces_signature_elements_dfcsign
    ADD CONSTRAINT defaces_signature_elements_dfcsign_elements_dfcsign_id_fkey FOREIGN KEY (elements_dfcsign_id) REFERENCES elements_dfcsign(id);


--
-- Name: public; Type: ACL; Schema: -; Owner: postgres
--

REVOKE ALL ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON SCHEMA public FROM postgres;
GRANT ALL ON SCHEMA public TO postgres;
GRANT ALL ON SCHEMA public TO PUBLIC;


--
-- PostgreSQL database dump complete
--

