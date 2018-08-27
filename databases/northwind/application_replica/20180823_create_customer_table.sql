create or replace sequence customers_sequence;

create table customers (
  id number default customers_sequence.nextval,
  company varchar(50) null default null,
  last_name varchar(50) null default null,
  first_name varchar(50) null default null,
  email_address varchar(50) null default null,
  job_title varchar(50) null default null,
  business_phone varchar(25) null default null,
  home_phone varchar(25) null default null,
  mobile_phone varchar(25) null default null,
  fax_number varchar(25) null default null,
  address text null default null,
  city varchar(50) null default null,
  state_province varchar(50) null default null,
  zip_postal_code varchar(15) null default null,
  country_region varchar(50) null default null,
  web_page text null default null,
  notes text null default null,
  attachments varbinary null)
