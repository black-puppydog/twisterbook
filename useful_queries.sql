-- these are the posts for which we have an RT or a reply, but not the original
select count(distinct p.parent_post_k, u.username)
  from posts as p
  inner join users as u on p.parent_post_username=u.username
  where p.post_type<>'normal' and p.parent_post_username IS NOT NULL and p.parent_post_k>-1 and (p.parent_post_k, u.id) not in (select k, userid from posts);

-- these are the users for which we have at least one post, and which could use a refresh
-- make sure to adjust the time in the "where" clause
SELECT username, id, last_indexed_k, last_indexed_time
  FROM users as u
  WHERE unix_timestamp(u.last_indexed_time) + 24*3600 <= unix_timestamp(now()) and last_indexed_k > -1
  ORDER BY u.last_indexed_time ASC, RAND();
