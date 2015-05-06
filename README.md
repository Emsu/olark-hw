# olark-hw

Run the following command `python main.py <path-to-input-file>`

## Thoughts
I think this task is very interesting because I can see how it'd be needed at Olark. I imagine there is some sort of stream parser like Spark or Storm that updates data in an aggregation phase and then a service probably aggregates the data on demand for the user and caches it. The cache is probably invalidated when a new event comes through that affects the data.

## Notes on solution
I essentially separate the the task into a few phases. The first phase is transforming the data for our input specific representation to an iterable of Python objects. This allows us to switch from flat file to other inputs relatively easily. As we only have to worry about handling data on a per site basis, I create a `SiteState` object for each site and pass it messages to process. The SiteState holds all data necessary to generate the statistics the user wants to see. It has a switch between event types so we can extend it to handle new types of events relatively easily. The output is currently to stout via `print` so I created a print function for an iterable of `SiteStates`. This output function could easily be swapped out to chance the output format to JSON or any other popular message format.

If I had more time, I abstract and optimize the cache_message_counts call and separate the caching and the aggregation. The data could be stored in Redis or SQLite so that when the process fails, it can pick off from the last event it processed. If I was building it for high availability, I would probably use Storm or Spark to transform the data in real time and updating a running data structure. The data structures can be used on demand by reduce functions to create the metrics that the users want.
