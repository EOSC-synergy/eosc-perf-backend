import json
from .data_types import *
from .database import db
from .facade import facade

uploaders = [
    Uploader(identifier='dead beef', email='user1@example.com', name='Max Mustermann'),
    Uploader(identifier='do you believe in magic?', email='user@example.com', name='John Doe')
]
sites = [
    Site(short_name='rpi', name="rpi_long", address='192.168.1.2', description="My cool raspberry pi"),
    Site(short_name="terrapc", name="terra_long", address='127.0.0.1', description="My strong desktop PC")
]
benchmarks = [
    Benchmark(docker_name='user/bench:version', uploader=uploaders[0]),
    Benchmark(docker_name='user/otherbench:version', uploader=uploaders[0])
]
for i in range(1, 101):
    fake_docker_name = "user{}/bench{}:version".format(i, i)
    benchmarks.append(Benchmark(docker_name=fake_docker_name, uploader=uploaders[i%2]))

tags = [
    Tag(name='neato'),
    Tag(name='cpu')
]

#results = []
#for uploader in uploaders:
#   for site in sites:
#        for benchmark in benchmarks:
#             for tag in tags:
#                result = Result(json="{}", uploader=uploader, site=site, benchmark=benchmark, tags=[tag])
#                results.append(result)

# generate a series of results with values for testing the diagram
data_results = []
for i in range(1, 17):
    # Numbers generated by Amdahl's Law, 1/(1-p+p/s) where p = 0.75, s = corecount
    p = 0.75
    d = {
        'user_args': {
            'num_gpus': i
        },
        'evaluation': {
            'result': {
                # generated following amdahl's law
                'average_examples_per_sec': 1/(1-p+p/i)
            }
        }
    }
    data_results.append(Result(json=json.dumps(d), uploader=uploaders[0], site=sites[0], benchmark=benchmarks[0], tags=[tags[0], tags[1]]))

def add_dummies_if_not_exist():
    for uploader in uploaders:
        facade.add_uploader(json.dumps({
            'id': uploader.get_id(),
            'email': uploader.get_email(),
            'name': uploader.get_name()
        }))

    for site in sites:
        facade.add_site(json.dumps({
            'short_name': site.get_short_name(),
            'address': site.get_address(),
            'name': site.get_name(),
            'description': site.get_description()
        }))

    for tag in tags:
        facade.add_tag(tag.get_name())

    for benchmark in benchmarks:
        facade.add_benchmark(benchmark.get_docker_name(), benchmark.get_uploader().get_id())

    #for result in results:
    #    facade.add_result(result.get_json(), json.dumps({
    #        'uploader': result.get_uploader().get_id(),
    #        'site': result.get_site().get_short_name(),
    #        'benchmark': result.get_benchmark().get_docker_name(),
    #        'tags': [tag.get_name() for tag in result.get_tags()]
    #    }))

    for result in data_results:
        facade.add_result(result.get_json(), json.dumps({
            'uploader': result.get_uploader().get_id(),
            'site': result.get_site().get_short_name(),
            'benchmark': result.get_benchmark().get_docker_name(),
            'tags': [tag.get_name() for tag in result.get_tags()]
        }))

    # make data added up to this point visible and useable
    iterator = ResultIterator(db.session)
    for result in iterator:
        result.set_hidden(False)
    for site in facade.get_sites():
        site.set_hidden(False)
    for bench in facade.get_benchmarks():
        bench.set_hidden(False)

    # add new 
    report_example_bench = Benchmark(docker_name='pihole/pihole:dev', uploader=uploaders[0])
    bench_report = BenchmarkReport(benchmark=report_example_bench, uploader=uploaders[0])
    facade.add_benchmark(report_example_bench.get_docker_name(), report_example_bench.get_uploader().get_id())

    report_example_site = Site('foobar', 'elsewhere')
    site_report = SiteReport(site=report_example_site, uploader=uploaders[0])
    facade.add_site(json.dumps({
        'short_name': report_example_site.get_short_name(),
        'address': report_example_site.get_address()
    }))

    facade.add_report(json.dumps({
        'message': 'Oopsie',
        'type': 'benchmark',
        'value': report_example_bench.get_docker_name(),
        'uploader': bench_report.get_reporter().get_id()
    }))
    facade.add_report(json.dumps({
        'message': 'Woopsie',
        'type': 'site',
        'value': site_report.get_site().get_short_name(),
        'uploader': site_report.get_reporter().get_id()
    }))
